using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class Perceptron
    {
        public double[] Weights { private set; get; }
        private double m_learningRate;

        public Perceptron(Random rand, int numInputs, double learningRate)
        {
            Weights = new double[numInputs + 1];
            // Random starting weights between -.5 and .5
            for (int i = 0; i < Weights.Length; ++i)
                Weights[i] = rand.NextDouble() - 0.5;
            m_learningRate = learningRate;
        }

        public void train(double[] inputs, double target)
        {
            double output = predict(inputs);
            double weightUpdateFactor = m_learningRate * (target - output);
            for (int i = 0; i < inputs.Length; ++i)
                Weights[i] += weightUpdateFactor * inputs[i];
            Weights[inputs.Length] += weightUpdateFactor;
        }

        public double predict(double[] inputs)
        {
            return threshold(calculateNet(inputs));
        }

        private double threshold(double netValue)
        {
            if (netValue > 0)
                return 1;
            return 0;
        }

        public double calculateNet(double[] inputs)
        {
            double netValue = 0;
            for (int i = 0; i < inputs.Length; ++i)
                netValue += inputs[i] * Weights[i];
            netValue += Weights[inputs.Length];
            return netValue;
        }
    }

    class PerceptronLearner : SupervisedLearner
    {
        private Perceptron m_perceptron;
        private Random m_rand;
        private double m_learningRate;
        private System.IO.StreamWriter m_outFile;

        public PerceptronLearner(double learningRate, Random rand, System.IO.StreamWriter outFile)
        {
            m_rand = rand;
            m_learningRate = learningRate;
            m_outFile = outFile;
        }

        public override void train(Matrix features, Matrix labels)
        {
            if (features.rows() != labels.rows())
            {
                throw (new Exception("Expected the features and labels to have the same number of rows"));
            }
            if (labels.cols() != 1)
            {
                throw (new Exception("Sorry, this method currently only supports one-dimensional labels"));
            }
            if (features.rows() == 0)
            {
                throw (new Exception("Expected at least one row"));
            }

            bool plotMisclassificationRate = labels.valueCount(0) != 0;
            bool plotDecisionLineWithInstances = labels.valueCount(0) == 2 && features.cols() == 2;

            m_perceptron = new Perceptron(m_rand, features.cols(), m_learningRate);

            Matrix order = new Matrix();
            order.setSize(features.rows(), 1);
            for (int i = 0; i < order.rows(); ++i)
                order.set(i, 0, i);

            if (m_outFile != null && plotMisclassificationRate)
            {
                m_outFile.WriteLine("set term wxt 0\nunset key");
                m_outFile.WriteLine("set yrange [0: 1]");
                m_outFile.WriteLine("set title \"Misclassification Rate vs. Epochs\"");
                m_outFile.WriteLine("set xlabel \"Epochs Completed\"");
                m_outFile.WriteLine("set ylabel \"Misclassification Rate\"");
                m_outFile.WriteLine("plot '-' with line lt 3");
            }

            int steadyEpochs = 0;
            int epochCount = 0;
            double accuracy = measureAccuracy(features, labels, new Matrix());
            while (steadyEpochs < 10)
            {
                order.shuffle(m_rand);
                for (int i = 0; i < order.rows(); ++i)
                {
                    int rowToUse = (int)order.get(i, 0);
                    m_perceptron.train(features.row(rowToUse), labels.get(rowToUse, 0));
                }
                epochCount++;
                double newAccuracy = measureAccuracy(features, labels, new Matrix());
                if (newAccuracy - accuracy < 0.1)
                    steadyEpochs++;
                else
                    steadyEpochs = 0;
                if (m_outFile != null && plotMisclassificationRate)
                {
                    m_outFile.WriteLine((epochCount - 1) + ", " + (1 - accuracy)
                        + " " + epochCount + ", " + (1 - newAccuracy));
                }
                accuracy = newAccuracy;
            }
            Console.WriteLine("Training took " + epochCount + " epochs.");
            Console.WriteLine("Final Weights:");
            for (int i = 0; i < features.cols(); ++i)
                Console.WriteLine(features.attrName(i) + " - " + m_perceptron.Weights[i]);
            Console.WriteLine("Bias Weight - " + m_perceptron.Weights[features.cols()]);

            if (m_outFile != null)
            {
                if (plotMisclassificationRate)
                    m_outFile.WriteLine("e");
                if (plotDecisionLineWithInstances)
                {
                    m_outFile.WriteLine("set term wxt 1");
                    m_outFile.WriteLine("set xrange[" + features.columnMin(0) + ": "
                        + features.columnMax(0) + "]");
                    m_outFile.WriteLine("set yrange[" + features.columnMin(1) + ": "
                        + features.columnMax(1) + "]");
                    m_outFile.WriteLine("set xlabel \"" + features.attrName(0) + "\"");
                    m_outFile.WriteLine("set ylabel \"" + features.attrName(1) + "\"");
                    m_outFile.WriteLine("unset key\nset size square\nset multiplot");
                    m_outFile.WriteLine("set title \"Instances and Decision Line\"");
                    m_outFile.WriteLine("# Final Weight Vector: " + m_perceptron.Weights[0] + " " + m_perceptron.Weights[1]
                        + " " + m_perceptron.Weights[2]);
                    m_outFile.WriteLine("plot " + (m_perceptron.Weights[0] / -m_perceptron.Weights[1]) + " * x + "
                        + (m_perceptron.Weights[2] / -m_perceptron.Weights[1]) + " linecolor rgb \"blue\"");
                    for (int i = 0; i < features.rows(); ++i)
                    {
                        if (labels.get(i, 0) == 1)
                            m_outFile.WriteLine("plot '-' with points pt 5 lc rgb \"dark-green\"");
                        else
                            m_outFile.WriteLine("plot '-' with points pt 5 lc rgb \"red\"");

                        m_outFile.WriteLine(features.get(i, 0) + " " + features.get(i, 1));
                        m_outFile.WriteLine("e");
                    }
                    m_outFile.WriteLine("unset multiplot");
                }
            }
        }

        public override void predict(double[] features, double[] labels)
        {
            if (labels.Length != 1)
            {
                throw (new Exception("Sorry, this method currently only supports one-dimensional labels"));
            }

            labels[0] = m_perceptron.predict(features);
        }
    }
}
