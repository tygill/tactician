using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class BackpropagationLearner : SupervisedLearner
    {
        private Random m_rand;
        private double m_learningRate;
        private BackpropagationLayer[] m_layers;
        private int m_numHiddenNodes;
        private double m_momentum;
        private StreamWriter m_outFile;

        public BackpropagationLearner(double learningRate, int numHiddenLayers, Random rand, StreamWriter outFile,
            double momentum = 0)
            : this(learningRate, numHiddenLayers, -1, rand, outFile, momentum)
        {
        }

        public BackpropagationLearner(double learningRate, int numHiddenLayers, int numHiddenNodes,
            Random rand, StreamWriter outFile, double momentum = 0)
        {
            m_learningRate = learningRate;
            m_rand = rand;
            m_layers = new BackpropagationLayer[numHiddenLayers + 1];
            m_numHiddenNodes = numHiddenNodes;
            m_momentum = momentum;
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

            initializeLayers(features.cols(), labels.valueCount(0));

            Matrix order = new Matrix();
            order.setSize(features.rows(), 1);
            for (int i = 0; i < order.rows(); ++i)
                order.set(i, 0, i);
            order.shuffle(m_rand);

            int numTrain = (int)(0.8 * (double)order.rows());
            Matrix trainOrder = new Matrix(order, 0, 0, numTrain, 1);
            Matrix validationFeatures = new Matrix(features, (int)order.get(numTrain, 0), 0, 1, features.cols());
            Matrix validationLabels = new Matrix(labels, (int)order.get(numTrain, 0), 0, 1, 1);
            for (int i = numTrain + 1; i < order.rows(); ++i)
            {
                validationFeatures.add(features, (int)order.get(i, 0), 0, 1);
                validationLabels.add(labels, (int)order.get(i, 0), 0, 1);
            }

            if (m_outFile != null)
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
            double accuracy = measureAccuracy(validationFeatures, validationLabels, new Matrix());
            while (steadyEpochs < 50)
            {
                trainOrder.shuffle(m_rand);
                for (int i = 0; i < trainOrder.rows(); ++i)
                {
                    int rowToUse = (int)trainOrder.get(i, 0);
                    double targetValue = labels.get(rowToUse, 0);
                    double[] inputs = features.row(rowToUse);
                    double[] outputs = getOutputs(inputs);
                    double[] prevErrors = new double[outputs.Length];
                    prevErrors[(int)targetValue] = 1;
                    for (int j = 0; j < prevErrors.Length; ++j)
                    {
                        prevErrors[j] -= outputs[j];
                        prevErrors[j] *= outputs[j] * (1 - outputs[j]);
                    }
                    int prev = m_layers.Length - 1;
                    int cur = prev - 1;

                    while (cur >= 0)
                    {
                        double[] curErrors = new double[m_layers[cur].NumNodes];
                        outputs = m_layers[cur].getLastPrediction();
                        for (int j = 0; j < curErrors.Length; ++j)
                        {
                            curErrors[j] = 0;
                            for (int k = 0; k < prevErrors.Length; ++k)
                                curErrors[j] += m_layers[prev].getWeight(j, k) * prevErrors[k];
                            curErrors[j] *= outputs[j] * (1 - outputs[j]);
                        }
                        m_layers[prev--].updateWeights(outputs, prevErrors, m_momentum);
                        prevErrors = curErrors;
                        cur--;
                    }
                    m_layers[prev].updateWeights(inputs, prevErrors, m_momentum);
                }
                epochCount++;
                double newAccuracy = measureAccuracy(validationFeatures, validationLabels, new Matrix());
                if (newAccuracy - accuracy < 0.1)
                    steadyEpochs++;
                else
                    steadyEpochs = 0;
                if (m_outFile != null)
                {
                    m_outFile.WriteLine((epochCount - 1) + ", " + (1 - accuracy)
                        + " " + epochCount + ", " + (1 - newAccuracy));
                }
                accuracy = newAccuracy;
            }
            Console.WriteLine("Training took " + epochCount + " epochs.");
            if (m_outFile != null)
                m_outFile.WriteLine("e");
        }

        private void initializeLayers(int numInputs, int numOutputs)
        {
            if (m_layers.Length > 1)
            {
                if (m_numHiddenNodes == -1)
                    m_numHiddenNodes = numInputs * 2;
                m_layers[0] = new BackpropagationLayer(m_rand, m_numHiddenNodes, numInputs, m_learningRate);
                for (int i = 1; i < m_layers.Length - 1; ++i)
                    m_layers[i] = new BackpropagationLayer(m_rand, m_numHiddenNodes, m_numHiddenNodes, m_learningRate);
                m_layers[m_layers.Length - 1] = new BackpropagationLayer(m_rand, numOutputs, m_numHiddenNodes, m_learningRate);
            }
            else
                m_layers[0] = new BackpropagationLayer(m_rand, numOutputs, numInputs, m_learningRate);
        }

        private double[] getOutputs(double[] features)
        {
            double[] outputs = m_layers[0].predict(features);
            for (int i = 1; i < m_layers.Length; ++i)
                outputs = m_layers[i].predict(outputs);
            return outputs;
        }

        public override void predict(double[] features, double[] labels)
        {
            if (labels.Length != 1)
            {
                throw (new Exception("Sorry, this method currently only supports one-dimensional labels"));
            }

            double[] outputs = getOutputs(features);
            int max = 0;
            for (int i = 1; i < outputs.Length; ++i)
                if (outputs[i] > outputs[max])
                    max = i;

            labels[0] = max;
        }
    }
}
