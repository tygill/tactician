using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class SigmoidUnit : ThresholdedUnit
    {
        private class SigmoidThresholder : IThresholder
        {
            public double thresholdValue(double val)
            {
                return 1 / (1 + Math.Exp(-val));
            }
        }

        public SigmoidUnit(Random rand, int numInputs, double learningRate)
            : base(rand, numInputs, learningRate, new SigmoidThresholder())
        {
        }
    }
}
