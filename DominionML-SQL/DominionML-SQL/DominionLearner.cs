using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public static class LearnerFactory
    {
        public enum Learners { Backprop, Perceptron }
        public static Learners Learner { get; set; }

        static LearnerFactory() {
            Learner = Learners.Backprop;
        }

        public static DominionLearner CreateDominionLearner(string card, IList<string> features, double[] boosts, bool sigmoidOutputs)
        {
            switch (Learner)
            {
                default:
                case Learners.Backprop:
                    return new BackpropagationLearner(card, features, boosts, sigmoidOutputs);
                case Learners.Perceptron:
                    return new PerceptronLearner(card, features);
            }
        }

        public static string Folder
        {
            get
            {
                switch (Learner)
                {
                    default:
                    case Learners.Backprop:
                        return BackpropagationLearner.LogFolder;
                    case Learners.Perceptron:
                        return PerceptronLearner.LogFolder;
                }
            }
        }
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
