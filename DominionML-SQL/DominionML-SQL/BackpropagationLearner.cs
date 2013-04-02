﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class BackpropagationLearner : DominionLearner
    {
        public BackpropNetwork Backprop { get; private set; }

        public BackpropagationLearner(string card, IList<string> inputs, int outputs, BackpropNetwork.HiddenLayerSize hiddenLayerSize = null, int layers = 1)
            : base(card)
        {
            Backprop = new BackpropNetwork();
            // Initialize the network now...
            // This may eventually be replaced with code that initializes it from a serialized file
            Backprop.Init(inputs, outputs, hiddenLayerSize, layers);
        }

        public override void TrainInstance(double[] features, double label)
        {
            Backprop.Train(features, label);
        }

        public override double Predict(double[] features)
        {
            return Backprop.Predict(features);
        }

        public override string Folder { get { return "Backprop"; } }

        public override string Serialize()
        {
            StringBuilder builder = new StringBuilder();
            Backprop.Serialize(builder);
            return builder.ToString();
        }

        public override void Load(string serialized)
        {
            throw new NotImplementedException();
        }

        public override void Dispose()
        {
            Backprop.Dispose();
            Backprop = null;
        }
    }
}
