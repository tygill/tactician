using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class BackpropogationLearner : SupervisedLearner
    {
        private Random m_rand;
        private double m_learningRate;
        private SigmoidUnit[][] m_hiddenNodes;
        private SigmoidUnit[] m_outputNodes;

        public BackpropogationLearner(double learningRate, int numHiddenLayers, int numHiddenNodes,
            Random rand)
        {
            m_learningRate = learningRate;
            m_rand = rand;
            m_hiddenNodes = new SigmoidUnit[numHiddenLayers][];
            for (int i = 0; i < m_hiddenNodes.Length; ++i)
                m_hiddenNodes[i] = new SigmoidUnit[numHiddenNodes];
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

            initializeSigmoidUnits(labels.valueCount(0), features.cols());

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

            int steadyEpochs = 0;
            int epochCount = 0;
            double accuracy = measureAccuracy(validationFeatures, validationLabels, new Matrix());
            while (steadyEpochs < 20)
            {
                trainOrder.shuffle(m_rand);
                for (int i = 0; i < trainOrder.rows(); ++i)
                {
                    int rowToUse = (int)trainOrder.get(i, 0);
                    double[] inputs = features.row(rowToUse);
                    double[] outputs = getOutputs(inputs);
                    double[] nextLayerError = new double[m_outputNodes.Length];
                    for (int j = 0; j < m_outputNodes.Length; ++j)
                    {
                        double targetValue = labels.get(rowToUse, 0);
                        double output = m_outputNodes[j].predict(inputs);
                        nextLayerError[j] = (targetValue - output) * output * (1 - output);
                        //This is using the wrong inputs. We need the inputs from the hidden layer before this.
                        m_outputNodes[j].updateWeights(inputs, nextLayerError[j]);
                    }
                    for (int hidLyr = m_hiddenNodes.Length - 1; hidLyr >= 0; --hidLyr)
                    {
                        double[] thisLayerError = new double[m_hiddenNodes[hidLyr].Length];
                        for (int k = 0; k < m_hiddenNodes[hidLyr].Length; ++k)
                        {
                            double error = 0;
                            for (int h = 0; h < nextLayerError.Length; ++h)
                            {
                                SigmoidUnit nodeh;
                                if (hidLyr == m_hiddenNodes.Length - 1)
                                    nodeh = m_outputNodes[h];
                                else
                                    nodeh = m_hiddenNodes[hidLyr + 1][h];
                                error += nodeh.Weights[k] * nextLayerError[h];
                            }
                            //error *= 
                        }
                    }
                }
                epochCount++;
                double newAccuracy = measureAccuracy(features, labels, new Matrix());
                if (newAccuracy - accuracy < 0.1)
                    steadyEpochs++;
                else
                    steadyEpochs = 0;
                accuracy = newAccuracy;
            }
        }

        private void initializeSigmoidUnits(int numInputs, int numOutputs)
        {
            for (int j = 0; j < m_hiddenNodes[0].Length; ++j)
                m_hiddenNodes[0][j] = new SigmoidUnit(m_rand, numInputs, m_learningRate);

            int numHiddenInputs = m_hiddenNodes[0].Length;
            for (int i = 1; i < m_hiddenNodes.Length; ++i)
            {
                numHiddenInputs = m_hiddenNodes[i - 1].Length;
                for (int j = 0; j < m_hiddenNodes[i].Length; ++j)
                    m_hiddenNodes[i][j] = new SigmoidUnit(m_rand, numHiddenInputs, m_learningRate);
            }

            m_outputNodes = new SigmoidUnit[numOutputs];
            for (int i = 0; i < m_outputNodes.Length; ++i)
                m_outputNodes[i] = new SigmoidUnit(m_rand, numHiddenInputs, m_learningRate);
        }

        private double[] getOutputs(double[] features)
        {
            double[] prevLayerOutput = new double[m_hiddenNodes[0].Length];
            for (int i = 0; i < m_hiddenNodes[0].Length; ++i)
                prevLayerOutput[i] = m_hiddenNodes[0][i].predict(features);
            for (int i = 1; i < m_hiddenNodes.Length; ++i)
            {
                double[] thisLayerOutput = new double[m_hiddenNodes[i].Length];
                for (int j = 0; j < m_hiddenNodes[i].Length; ++j)
                    thisLayerOutput[j] = m_hiddenNodes[i][j].predict(prevLayerOutput);
                prevLayerOutput = thisLayerOutput;
            }
            double[] outputs = new double[m_outputNodes.Length];
            for (int i = 0; i < m_outputNodes.Length; ++i)
                outputs[i] = m_outputNodes[i].predict(prevLayerOutput);
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
