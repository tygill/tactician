// ----------------------------------------------------------------
// The contents of this file are distributed under the CC0 license.
// See http://creativecommons.org/publicdomain/zero/1.0/
// ----------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MLToolkitCSharp
{
    public class MLSystemManager
    {
        /**
         *  When you make a new learning algorithm, you should add a line for it to this method.
         */
        public SupervisedLearner getLearner(string model, Random rand)
        {
            if (model.Equals("baseline", StringComparison.OrdinalIgnoreCase))
            {
                return new BaselineLearner();
            }
            /*
            else if (model.Equals("perceptron", StringComparison.OrdinalIgnoreCase))
            {
                return new Perceptron(rand);
            }
            else if (model.Equals("neuralnet", StringComparison.OrdinalIgnoreCase))
            {
                return new NeuralNet(rand);
            }
            else if (model.Equals("decisiontree", StringComparison.OrdinalIgnoreCase))
            {
                return new DecisionTree(rand);
            }
            else if (model.Equals("knn", StringComparison.OrdinalIgnoreCase))
            {
                return new InstanceBasedLearner(rand);
            }
            */
            else
            {
                throw new Exception("Unrecognized model: " + model);
            }
        }

        public void run(string[] args)
        {
            //args = new string[] { "-L", "baseline", "-A", "iris.arff", "-E", "cross", "10", "-N" };

            //Random rand = new Random(1234); // Use a seed for deterministic results (makes debugging easier)
            Random rand = new Random(); // No seed for non-deterministic results

            // Parse the command line arguments
            ArgParser parser = new ArgParser(args);
            string fileName = parser.ARFF; // File specified by the user
            string learnerName = parser.Learner; // Learning algorithm specified by the user
            string evalMethod = parser.Evaluation; // Evaluation method specified by the user
            string evalParameter = parser.EvalParameter; // Evaluation parameters specified by the user
            bool printConfusionMatrix = parser.Verbose;
            bool normalize = parser.Normalize;

            // Load the model
            SupervisedLearner learner = getLearner(learnerName, rand);

            // Load the ARFF file
            Matrix data = new Matrix();
            data.loadArff(fileName);
            if (normalize)
            {
                Console.WriteLine("Using normalized data\n");
                data.normalize();
            }

            // Print some stats
            Console.WriteLine();
            Console.WriteLine("Dataset name: " + fileName);
            Console.WriteLine("Number of instances: " + data.rows());
            Console.WriteLine("Number of attributes: " + data.cols());
            Console.WriteLine("Learning algorithm: " + learnerName);
            Console.WriteLine("Evaluation method: " + evalMethod);
            Console.WriteLine();

            if (evalMethod.Equals("training", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine("Calculating accuracy on training set...");
                Matrix features = new Matrix(data, 0, 0, data.rows(), data.cols() - 1);
                Matrix labels = new Matrix(data, 0, data.cols() - 1, data.rows(), 1);
                Matrix confusion = new Matrix();
                Stopwatch stopwatch = new Stopwatch();
                stopwatch.Start();
                learner.train(features, labels);
                stopwatch.Stop();
                Console.WriteLine("Time to train (in seconds): " + stopwatch.Elapsed.TotalSeconds);
                double accuracy = learner.measureAccuracy(features, labels, confusion);
                Console.WriteLine("Training set accuracy: " + accuracy);
                if (printConfusionMatrix)
                {
                    Console.WriteLine("\nConfusion matrix: (Row=target value, Col=predicted value)");
                    confusion.print();
                    Console.WriteLine("\n");
                }
            }
            else if (evalMethod.Equals("static", StringComparison.OrdinalIgnoreCase))
            {
                Matrix testData = new Matrix();
                testData.loadArff(evalParameter);
                if (normalize)
                {
                    testData.normalize(); // BUG! This may normalize differently from the training data. It should use the same ranges for normalization!
                }

                Console.WriteLine("Calculating accuracy on separate test set...");
                Console.WriteLine("Test set name: " + evalParameter);
                Console.WriteLine("Number of test instances: " + testData.rows());
                Matrix features = new Matrix(data, 0, 0, data.rows(), data.cols() - 1);
                Matrix labels = new Matrix(data, 0, data.cols() - 1, data.rows(), 1);
                Stopwatch stopwatch = new Stopwatch();
                stopwatch.Start();
                learner.train(features, labels);
                stopwatch.Stop();
                Console.WriteLine("Time to train (in seconds): " + stopwatch.Elapsed.TotalSeconds);
                double trainAccuracy = learner.measureAccuracy(features, labels, null);
                Console.WriteLine("Training set accuracy: " + trainAccuracy);
                Matrix testFeatures = new Matrix(testData, 0, 0, testData.rows(), testData.cols() - 1);
                Matrix testLabels = new Matrix(testData, 0, testData.cols() - 1, testData.rows(), 1);
                Matrix confusion = new Matrix();
                double testAccuracy = learner.measureAccuracy(testFeatures, testLabels, confusion);
                Console.WriteLine("Test set accuracy: " + testAccuracy);
                if (printConfusionMatrix)
                {
                    Console.WriteLine("\nConfusion matrix: (Row=target value, Col=predicted value)");
                    confusion.print();
                    Console.WriteLine("\n");
                }
            }
            else if (evalMethod.Equals("random", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine("Calculating accuracy on a random hold-out set...");
                double trainPercent = 1 - double.Parse(evalParameter);
                if (trainPercent < 0 || trainPercent > 1)
                    throw new Exception("Percentage for random evaluation must be between 0 and 1");
                Console.WriteLine("Percentage used for training: " + trainPercent);
                Console.WriteLine("Percentage used for testing: " + double.Parse(evalParameter));
                data.shuffle(rand);
                int trainSize = (int)(trainPercent * data.rows());
                Matrix trainFeatures = new Matrix(data, 0, 0, trainSize, data.cols() - 1);
                Matrix trainLabels = new Matrix(data, 0, data.cols() - 1, trainSize, 1);
                Matrix testFeatures = new Matrix(data, trainSize, 0, data.rows() - trainSize, data.cols() - 1);
                Matrix testLabels = new Matrix(data, trainSize, data.cols() - 1, data.rows() - trainSize, 1);
                Stopwatch stopwatch = new Stopwatch();
                stopwatch.Start();
                learner.train(trainFeatures, trainLabels);
                stopwatch.Stop();
                Console.WriteLine("Time to train (in seconds): " + stopwatch.Elapsed.TotalSeconds);
                double trainAccuracy = learner.measureAccuracy(trainFeatures, trainLabels, null);
                Console.WriteLine("Training set accuracy: " + trainAccuracy);
                Matrix confusion = new Matrix();
                double testAccuracy = learner.measureAccuracy(testFeatures, testLabels, confusion);
                Console.WriteLine("Test set accuracy: " + testAccuracy);
                if (printConfusionMatrix)
                {
                    Console.WriteLine("\nConfusion matrix: (Row=target value, Col=predicted value)");
                    confusion.print();
                    Console.WriteLine("\n");
                }
            }
            else if (evalMethod.Equals("cross", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine("Calculating accuracy using cross-validation...");
                int folds = int.Parse(evalParameter);
                if (folds <= 0)
                    throw new Exception("Number of folds must be greater than 0");
                Console.WriteLine("Number of folds: " + folds);
                int reps = 1;
                double sumAccuracy = 0.0;
                double elapsedTime = 0.0;
                for (int j = 0; j < reps; j++)
                {
                    data.shuffle(rand);
                    for (int i = 0; i < folds; i++)
                    {
                        int begin = i * data.rows() / folds;
                        int end = (i + 1) * data.rows() / folds;
                        Matrix trainFeatures = new Matrix(data, 0, 0, begin, data.cols() - 1);
                        Matrix trainLabels = new Matrix(data, 0, data.cols() - 1, begin, 1);
                        Matrix testFeatures = new Matrix(data, begin, 0, end - begin, data.cols() - 1);
                        Matrix testLabels = new Matrix(data, begin, data.cols() - 1, end - begin, 1);
                        trainFeatures.add(data, end, 0, data.rows() - end);
                        trainLabels.add(data, end, data.cols() - 1, data.rows() - end);
                        Stopwatch stopwatch = new Stopwatch();
                        stopwatch.Start();
                        learner.train(trainFeatures, trainLabels);
                        stopwatch.Stop();
                        elapsedTime += stopwatch.Elapsed.TotalSeconds;
                        double accuracy = learner.measureAccuracy(testFeatures, testLabels, null);
                        sumAccuracy += accuracy;
                        Console.WriteLine("Rep=" + j + ", Fold=" + i + ", Accuracy=" + accuracy);
                    }
                }
                elapsedTime /= (reps * folds);
                Console.WriteLine("Average time to train (in seconds): " + elapsedTime);
                Console.WriteLine("Mean accuracy=" + (sumAccuracy / (reps * folds)));
            }
        }

        /**
	     * Class for parsing out the command line arguments
	     */
        private class ArgParser
        {
            // You can add more options for specific learning models if you wish
            public ArgParser(String[] argv)
            {
                try
                {

                    for (int i = 0; i < argv.Length; i++)
                    {

                        if (argv[i].Equals("-V"))
                        {
                            Verbose = true;
                        }
                        else if (argv[i].Equals("-N"))
                        {
                            Normalize = true;
                        }
                        else if (argv[i].Equals("-A"))
                        {
                            ARFF = argv[++i];
                        }
                        else if (argv[i].Equals("-L"))
                        {
                            Learner = argv[++i];
                        }
                        else if (argv[i].Equals("-E"))
                        {
                            Evaluation = argv[++i];
                            if (argv[i].Equals("static"))
                            {
                                //expecting a test set name
                                EvalParameter = argv[++i];
                            }
                            else if (argv[i].Equals("random"))
                            {
                                //expecting a double representing the percentage for testing
                                //Note stratification is NOT done
                                EvalParameter = argv[++i];
                            }
                            else if (argv[i].Equals("cross"))
                            {
                                //expecting the number of folds
                                EvalParameter = argv[++i];
                            }
                            else if (!argv[i].Equals("training"))
                            {
                                Console.WriteLine("Invalid Evaluation Method: " + argv[i]);
                                Environment.Exit(0);
                            }
                        }
                        else
                        {
                            Console.WriteLine("Invalid parameter: " + argv[i]);
                            Environment.Exit(0);
                        }
                    }

                }
                catch (Exception e)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E [evaluationMethod] {[extraParamters]} [OPTIONS]\n");
                    Console.WriteLine("OPTIONS:");
                    Console.WriteLine("-V Print the confusion matrix and learner accuracy on individual class values\n");

                    Console.WriteLine("Possible evaluation methods are:");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E training");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E static [testARFF_File]");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E random [%_ForTesting]");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E cross [numOfFolds]\n");
                    Environment.Exit(0);
                }

                if (ARFF == null || Learner == null || Evaluation == null)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E [evaluationMethod] {[extraParamters]} [OPTIONS]\n");
                    Console.WriteLine("OPTIONS:");
                    Console.WriteLine("-V Print the confusion matrix and learner accuracy on individual class values");
                    Console.WriteLine("-N Use normalized data");
                    Console.WriteLine();
                    Console.WriteLine("Possible evaluation methods are:");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E training");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E static [testARFF_File]");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E random [%_ForTesting]");
                    Console.WriteLine("MLSystemManager -L [learningAlgorithm] -A [ARFF_File] -E cross [numOfFolds]\n");
                    Environment.Exit(0);
                }
            }

            // C# style properties with getters and setters
            public string ARFF { private set; get; }
            public string Learner { private set; get; }
            public string Evaluation { private set; get; }
            public string EvalParameter { private set; get; }
            public bool Verbose { private set; get; }
            public bool Normalize { private set; get; }
        }

        public static void Main(string[] args)
        {
            MLSystemManager ml = new MLSystemManager();
            ml.run(args);
        }
    }
}
