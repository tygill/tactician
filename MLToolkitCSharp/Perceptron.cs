using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class Perceptron
    {
        private double[] m_weights;
        private double m_learningRate;

        public Perceptron(Random rand, int numInputs, double learningRate = 0.1)
        {
            m_weights = new double[numInputs + 1];
            // Random starting weights between -.5 and .5
            for (int i = 0; i < m_weights.Length; ++i)
                m_weights[i] = rand.NextDouble() - 0.5;
            m_learningRate = learningRate;
        }

        public void train(double[] inputs, double target)
        {
            double output = predict(inputs);
            double weightUpdateFactor = m_learningRate * (target - output);
            for (int i = 0; i < inputs.Length; ++i)
                m_weights[i] += weightUpdateFactor * inputs[i];
            m_weights[inputs.Length] += weightUpdateFactor;
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
                netValue += inputs[i] * m_weights[i];
            netValue += m_weights[inputs.Length];
            return netValue;
        }

        public void print(System.IO.StreamWriter outFile)
        {
            outFile.WriteLine("# Final Weight Vector: " + m_weights[0] + " " + m_weights[1] + " " + m_weights[2]);
            outFile.WriteLine("plot " + (m_weights[0] / -m_weights[1]) + " * x + "
                + (m_weights[2] / -m_weights[1]) + " linecolor rgb \"blue\"");
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

            m_perceptron = new Perceptron(m_rand, features.cols(), m_learningRate);

            Matrix order = new Matrix();
            order.setSize(features.rows(), 1);
            for (int i = 0; i < order.rows(); ++i)
                order.set(i, 0, i);

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
                if (newAccuracy <= accuracy)
                    steadyEpochs++;
                else
                    steadyEpochs = 0;
                accuracy = newAccuracy;
            }
            Console.WriteLine("Training took " + epochCount + " epochs.");

            if (m_outFile != null)
            {
                m_outFile.WriteLine("set xrange[" + features.columnMin(0) + ": "
                    + features.columnMax(0) + "]");
                m_outFile.WriteLine("set yrange[" + features.columnMin(1) + ": "
                    + features.columnMax(1) + "]");
                m_outFile.WriteLine("unset key\nset size square\nset multiplot");
                m_perceptron.print(m_outFile);
                for (int i = 0; i < features.rows(); ++i)
                {
                    if (labels.get(i, 0) == 1)
                        m_outFile.WriteLine("plot '-' with points pt 5 lc rgb \"dark-green\"");
                    else
                        m_outFile.WriteLine("plot '-' with points pt 5 lc rgb \"red\"");

                    m_outFile.WriteLine(features.get(i, 0) + " " + features.get(i, 1));
                    m_outFile.WriteLine("e");
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
