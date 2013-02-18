using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class ThresholdedUnit : LinearUnit
    {
        private IThresholder m_thresholder;

        public ThresholdedUnit(Random rand, int numInputs, double learningRate, IThresholder thresholder)
            : base(rand, numInputs, learningRate)
        {
            m_thresholder = thresholder;
        }

        public override double predict(double[] inputs)
        {
            return m_thresholder.thresholdValue(base.predict(inputs));
        }
    }
}
