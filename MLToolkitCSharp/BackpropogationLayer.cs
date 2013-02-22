using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class BackpropogationLayer
    {
        public int NumInputs { private set; get; }
        public int NumNodes { private set; get; }
        private SigmoidUnit[] m_nodes;
        private double[] m_lastPrediction;

        public BackpropogationLayer(Random rand, int numNodes, int numInputs, double learningRate)
        {
            NumNodes = numNodes;
            NumInputs = numInputs;

            m_nodes = new SigmoidUnit[NumNodes];
            for (int i = 0; i < NumNodes; ++i)
                m_nodes[i] = new SigmoidUnit(rand, NumInputs, learningRate);
        }

        public double[] predict(double[] inputs)
        {
            double[] outputs = new double[NumNodes];
            for (int i = 0; i < NumNodes; ++i)
                outputs[i] = m_nodes[i].predict(inputs);
            m_lastPrediction = outputs;
            return outputs;
        }

        public double[] getLastPrediction()
        {
            return m_lastPrediction;
        }

        public void updateWeights(double[] inputs, double[] errors, double momentum = 0)
        {
            for (int i = 0; i < m_nodes.Length; ++i)
                m_nodes[i].updateWeights(inputs, errors[i], momentum);
        }

        // Get the weight for the ith input going into node j.
        public double getWeight(int i, int j)
        {
            return m_nodes[j].Weights[i];
        }
    }
}
