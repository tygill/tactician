﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class LinearUnit
    {
        public double[] Weights { private set; get; }
        private double m_learningRate;
        private double[] m_lastWeightUpdate;

        public LinearUnit(Random rand, int numInputs, double learningRate)
        {
            Weights = new double[numInputs + 1];
            m_lastWeightUpdate = new double[numInputs + 1];
            // Random starting weights between -.5 and .5
            for (int i = 0; i < Weights.Length; ++i)
            {
                Weights[i] = rand.NextDouble() - 0.5;
                m_lastWeightUpdate[i] = 0;
            }
            m_learningRate = learningRate;
        }

        public void updateWeights(double[] inputs, double error, double momentum = 0)
        {
            double weightUpdateFactor = m_learningRate * error;
            for (int i = 0; i < inputs.Length; ++i)
            {
                double delta = weightUpdateFactor * inputs[i] + momentum * m_lastWeightUpdate[i];
                Weights[i] += delta;
                m_lastWeightUpdate[i] = delta;
            }
            double deltaBias = weightUpdateFactor + momentum * m_lastWeightUpdate[inputs.Length];
            Weights[inputs.Length] += deltaBias;
            m_lastWeightUpdate[inputs.Length] = deltaBias;
        }

        public virtual double predict(double[] inputs)
        {
            return calculateNet(inputs);
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
}
