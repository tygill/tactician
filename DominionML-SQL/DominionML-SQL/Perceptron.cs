using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace DominionML_SQL
{
    class LinearUnit
    {
        public Random Rand { get; private set; }
        public double[] Weights { private set; get; }
        public double LearningRate { private set; get; }
        private double[] m_lastWeightUpdate;

        public LinearUnit(double learningRate)
        {
            Rand = new Random();
            LearningRate = learningRate;
        }

        public void Init(IList<string> inputList)
        {
            int numInputs = inputList.Count;

            Weights = new double[numInputs + 1];
            m_lastWeightUpdate = new double[numInputs + 1];
            // Random starting weights between -.5 and .5
            for (int i = 0; i < Weights.Length; ++i)
            {
                Weights[i] = Rand.NextDouble() - 0.5;
                m_lastWeightUpdate[i] = 0;
            }
        }

        public void updateWeights(double[] inputs, double error, double speedUp = 0)
        {
            double weightUpdateFactor = LearningRate * error;
            for (int i = 0; i < inputs.Length; ++i)
            {
                double delta = weightUpdateFactor * inputs[i] + speedUp * m_lastWeightUpdate[i];
                Weights[i] += delta;
                m_lastWeightUpdate[i] = delta;
            }
            double deltaBias = weightUpdateFactor + speedUp * m_lastWeightUpdate[inputs.Length];
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

    interface IThresholder
    {
        double thresholdValue(double val);
    }

    class ThresholdedUnit : LinearUnit
    {
        private IThresholder m_thresholder;

        public ThresholdedUnit(IThresholder thresholder, double learningRate)
            : base(learningRate)
        {
            m_thresholder = thresholder;
        }

        public override double predict(double[] inputs)
        {
            return m_thresholder.thresholdValue(base.predict(inputs));
        }
    }

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

        public Perceptron(double learningRate = 0.1)
            : base(new PerceptronThresholder(), learningRate)
        {
        }
    }
}
