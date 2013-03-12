// ----------------------------------------------------------------
// The contents of this file are distributed under the CC0 license.
// See http://creativecommons.org/publicdomain/zero/1.0/
// ----------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MLToolkitCSharp
{
    public class BaselineLearner : SupervisedLearner
    {
        public double[] m_labels;

        public override void train(Matrix features, Matrix labels)
        {
            m_labels = new double[labels.cols()];
            for (int i = 0; i < labels.cols(); i++)
            {
                if (labels.valueCount(i) == 0)
                {
                    m_labels[i] = labels.columnMean(i); // continuous
                }
                else
                {
                    m_labels[i] = labels.mostCommonValue(i); // nominal
                }
            }
        }

        public override void predict(double[] features, double[] labels)
        {
            for (int i = 0; i < m_labels.Length; i++)
            {
                labels[i] = m_labels[i];
            }
        }
    }
}
