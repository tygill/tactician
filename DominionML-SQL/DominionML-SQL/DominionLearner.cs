using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public static class LearnerFactory
    {
        public static DominionLearner CreateDominionLearner(string card, IEnumerable<string> features)
        {
            return new BackpropagationLearner(card, features.Count(), 1);
        }
    }

    public abstract class DominionLearner
    {
        public string Card { get; private set; }

        public DominionLearner(string card)
        {
            Card = card;
        }

        public abstract void TrainInstance(double[] features, double label);

        public abstract double Predict(double[] features);

        public abstract string Serialize();

        public abstract void Load(string serialized);
    }
}
