using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class PerceptronLearner : SupervisedLearner
    {
        private Perceptron[] m_perceptrons;
        private Random m_rand;
        private double m_learningRate;
        private Plotter m_plotter;

        public PerceptronLearner(double learningRate, Random rand, Plotter plotter)
        {
            m_rand = rand;
            m_learningRate = learningRate;
            m_plotter = plotter;
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

            int numOutputClasses = labels.valueCount(0);

            bool plotMisclassificationRate = numOutputClasses != 0;
            bool plotDecisionLineWithInstances = numOutputClasses == 2 && features.cols() == 2;

            if (numOutputClasses > 2)
            {
                // Create one perceptron for each output class.
                m_perceptrons = new Perceptron[numOutputClasses];
                for (int i = 0; i < numOutputClasses; ++i)
                    m_perceptrons[i] = new Perceptron(m_rand, features.cols(), m_learningRate);
            }
            else
            {
                m_perceptrons = new Perceptron[1];
                m_perceptrons[0] = new Perceptron(m_rand, features.cols(), m_learningRate);
            }

            Matrix order = new Matrix();
            order.setSize(features.rows(), 1);
            for (int i = 0; i < order.rows(); ++i)
                order.set(i, 0, i);

            int steadyEpochs = 0;
            int epochCount = 0;
            double accuracy = measureAccuracy(features, labels, new Matrix());
            Plot misclassificationPlot = null;
            if (m_plotter != null && plotMisclassificationRate)
            {
                misclassificationPlot = new Plot("Misclassification Rate vs. Epochs");
                misclassificationPlot.XLabel = "Epochs Completed";
                misclassificationPlot.YLabel = "Misclassification Rate";
                misclassificationPlot.YMin = 0;
                misclassificationPlot.YMax = 1;
                misclassificationPlot.addDataPoint(epochCount, 1 - accuracy);
                m_plotter.addPlot(misclassificationPlot);
            }
            while (steadyEpochs < 10)
            {
                order.shuffle(m_rand);
                for (int i = 0; i < order.rows(); ++i)
                {
                    int rowToUse = (int)order.get(i, 0);
                    for (int j = 0; j < m_perceptrons.Length; ++j)
                    {
                        double targetValue = labels.get(rowToUse, 0);
                        if (m_perceptrons.Length > 1)
                        {
                            if ((int)targetValue == j)
                                targetValue = 1;
                            else
                                targetValue = 0;
                        }
                        double[] inputs = features.row(rowToUse);
                        double error = targetValue - m_perceptrons[j].predict(inputs);
                        m_perceptrons[j].updateWeights(inputs, error);
                    }
                }
                epochCount++;
                double newAccuracy = measureAccuracy(features, labels, new Matrix());
                if (newAccuracy - accuracy < 0.1)
                    steadyEpochs++;
                else
                    steadyEpochs = 0;
                accuracy = newAccuracy;
                if (misclassificationPlot != null && plotMisclassificationRate)
                    misclassificationPlot.addDataPoint(epochCount, 1 - accuracy);
            }
            Console.WriteLine("Training took " + epochCount + " epochs.");
            /*for (int j = 0; j < m_perceptrons.Length; ++j)
            {
                Console.WriteLine("\nFinal Weights (Perceptron " + j + "):");
                for (int i = 0; i < features.cols(); ++i)
                    Console.WriteLine("\t" + features.attrName(i) + ": " + m_perceptrons[j].Weights[i]);
                Console.WriteLine("\tBias Weight: " + m_perceptrons[j].Weights[features.cols()]);
            }*/

            /*
            if (m_outFile != null)
            {
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
                    m_outFile.WriteLine("# Final Weight Vector: " + m_perceptrons[0].Weights[0] + " " + m_perceptrons[0].Weights[1]
                        + " " + m_perceptrons[0].Weights[2]);
                    m_outFile.WriteLine("plot " + (m_perceptrons[0].Weights[0] / -m_perceptrons[0].Weights[1]) + " * x + "
                        + (m_perceptrons[0].Weights[2] / -m_perceptrons[0].Weights[1]) + " linecolor rgb \"blue\"");
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
            */
        }

        public override void predict(double[] features, double[] labels)
        {
            if (labels.Length != 1)
            {
                throw (new Exception("Sorry, this method currently only supports one-dimensional labels"));
            }

            if (m_perceptrons.Length == 1)
            {
                labels[0] = m_perceptrons[0].predict(features);
            }
            else
            {
                int prediction = -1;
                for (int i = 0; i < m_perceptrons.Length; ++i)
                {
                    if ((int)m_perceptrons[i].predict(features) == 1)
                    {
                        if (prediction != -1)  // Another perceptron already output high
                        {
                            double ourNet = m_perceptrons[i].calculateNet(features);
                            double theirNet = m_perceptrons[prediction].calculateNet(features);
                            if (ourNet > theirNet)
                                prediction = i;
                        }
                        else
                        {
                            prediction = i;
                        }
                    }
                }
                if (prediction == -1) // None of the perceptrons output high.
                {
                    prediction = 0;
                    double highestNet = m_perceptrons[0].calculateNet(features);
                    for (int i = 1; i < m_perceptrons.Length; ++i)
                    {
                        double net = m_perceptrons[i].calculateNet(features);
                        if (net > highestNet)
                        {
                            highestNet = net;
                            prediction = i;
                        }
                    }
                }
                labels[0] = prediction;
            }
        }
    }
}
