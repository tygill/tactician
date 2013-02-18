using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class Perceptron : ThresholdedUnit
    {
        private class PerceptronThresholder : IThresholder
        {
            private double m_high, m_low;

            public PerceptronThresholder(double high = 1, double low = 0)
            {
                m_high = high;
                m_low = low;
            }

            public double thresholdValue(double netValue)
            {
                if (netValue > 0)
                    return m_high;
                return m_low;
            }
        }

        public Perceptron(Random rand, int numInputs, double learningRate)
            : base(rand, numInputs, learningRate, new PerceptronThresholder())
        {
        }
    }
}
