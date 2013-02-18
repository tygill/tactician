using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class LinearUnit
    {
        public double[] Weights { private set; get; }
        private double m_learningRate;

        public LinearUnit(Random rand, int numInputs, double learningRate)
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
