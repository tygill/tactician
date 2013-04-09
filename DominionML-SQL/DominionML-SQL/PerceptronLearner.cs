using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace DominionML_SQL
{
    class PerceptronLearner : DominionLearner
    {
        private Perceptron perceptron;
        private IList<string> inputNames;

        public PerceptronLearner(string card, IList<string> inputs)
            : base(card)
        {
            perceptron = new Perceptron();
            perceptron.Init(inputs);
            inputNames = inputs;
        }

        public override void TrainInstance(double[] features, double label)
        {
            double error = label - perceptron.predict(features);
            perceptron.updateWeights(features, error);
        }

        public override double Predict(double[] features)
        {
            return perceptron.predict(features);
        }

        public static string LogFolder { get { return "Perceptron"; } }

        public override string Folder { get { return LogFolder; } }

        public override string Serialize()
        {
            StringBuilder builder = new StringBuilder();
            builder.Append("{");
            for (int i = 0; i < inputNames.Count; ++i)
                builder.Append("\"" + inputNames[i] + "\":" + perceptron.Weights[i] + ",");
            builder.Append("\"bias\":" + perceptron.Weights[perceptron.Weights.Length - 1] + "}");
            return builder.ToString();
        }

        public override void Load(string serialized)
        {
            throw new NotImplementedException();
        }

        public override void Dispose()
        {
        }
    }
}
