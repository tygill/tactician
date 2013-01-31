using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    class Perceptron : SupervisedLearner
    {
        public Perceptron(Random rand)
        {
        }

        public override void train(Matrix features, Matrix labels)
        {
        }

        public override void predict(double[] features, double[] labels)
        {
            for (int i = 0; i < labels.Length; i++)
            {
                labels[i] = 0;
            }
        }
    }
}
