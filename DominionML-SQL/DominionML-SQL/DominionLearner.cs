using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public static class LearnerFactory
    {
        public static DominionLearner CreateDominionLearner(string card, IList<string> features, double[] boosts, bool sigmoidOutputs)
        {
            return new BackpropagationLearner(card, features, boosts, sigmoidOutputs);
        }

        public static string Folder { get { return BackpropagationLearner.LogFolder; } }
    }

    public abstract class DominionLearner : IDisposable
    {
        public string Card { get; private set; }

        public DominionLearner(string card)
        {
            Card = card;
        }

        public abstract void TrainInstance(double[] features, double label);

        public abstract double Predict(double[] features);

        public abstract string Folder { get; }

        public abstract string Serialize();

        public abstract void Load(string serialized);

        public abstract void Dispose();
    }
}
