using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class BackpropNetwork
    {
        public delegate int HiddenLayerSize(int numInputs, int numOutputs, int layer, int numLayers);

        public static int nInputs(int numInputs, int numOutputs, int layer, int numLayers)
        {
            return numInputs;
        }

        public static int twoNInputs(int numInputs, int numOutputs, int layer, int numLayers)
        {
            return numInputs * 2;
        }

        public Random Rand { get; private set; }
        public BiasNode BiasNode { get; private set; }

        public double LearningRate { get; private set; }
        public double SpeedUp { get; private set; }
        public double MaxInitialWeight { get; private set; }


        private List<InputNode> inputNodes;
        private List<List<HiddenNode>> hiddenNodes;
        private List<OutputNode> outputNodes;

        public BackpropNetwork(double learningRate = 0.1, double speedUp = 0.0, double maxInitialWeight = 0.5)
        {
            LearningRate = learningRate;
            SpeedUp = speedUp;
            MaxInitialWeight = maxInitialWeight;

            Rand = new Random();
            BiasNode = new BiasNode(this);
            //Console.WriteLine("Training with Backpropagation");
            //Console.WriteLine("Learning Rate: {0}", LearningRate);
            //Console.WriteLine("Momentum/Speed Up: {0}", SpeedUp);
        }

        public void Init(int inputs, int outputs, HiddenLayerSize hiddenLayerSize = null, int layers = 1)
        {
            hiddenLayerSize = hiddenLayerSize == null ? nInputs : hiddenLayerSize;
            inputNodes = new List<InputNode>(inputs);
            hiddenNodes = new List<List<HiddenNode>>(layers);
            outputNodes = new List<OutputNode>(outputs);

            // Create the input nodes
            for (int i = 0; i < inputs; i++)
            {
                InputNode node = new InputNode(this);
                // This will line up each element of the inputNodes list with a feature, ordered by index number.
                inputNodes.Add(node);
            }
            //Console.WriteLine("Using {0} input nodes", inputs);

            // Create the hidden nodes
            for (int layer = 0; layer < layers; layer++)
            {
                int numHidden = hiddenLayerSize(inputs, outputs, layer, layers);
                List<HiddenNode> layerNodes = new List<HiddenNode>(numHidden);
                hiddenNodes.Add(layerNodes);
                for (int i = 0; i < numHidden; i++)
                {
                    HiddenNode node = new HiddenNode(this);
                    layerNodes.Add(node);
                    // Connect this new hidden node to all nodes in the previous layer
                    if (layer == 0)
                    {
                        // If this is the first layer, it gets connected to the input nots
                        inputNodes.ForEach(inputNode => node.Connect(inputNode));
                    }
                    else
                    {
                        // Otherwise it should connect to all the nodes in the layer before it
                        hiddenNodes[layer - 1].ForEach(hiddenNode => node.Connect(hiddenNode));
                    }
                }
                //Console.WriteLine("Using {0} hidden nodes in layer {1}", numHidden, layers);
            }

            // Create the output nodes (one for each possible value of the output)
            for (int i = 0; i < outputs; i++)
            {
                OutputNode node = new OutputNode(this);
                outputNodes.Add(node);
                // Connect this new output node to all the hidden nodes (assuming a single layer)
                hiddenNodes.Last().ForEach(hiddenNode => node.Connect(hiddenNode));
            }
            //Console.WriteLine("Using {0} output nodes", outputs);
        }

        public void Train(double[] features, double label)
        {
            // Plug in the inputs and outputs
            LoadInputs(features);
            // Assume a single output node
            outputNodes[0].Target = label;

            // Now that the inputs and outputs are set, mark them all to be updated again
            MarkNodesStale();
            // Now that all the outputs and errors are stale, they'll be recalculated when requested.
            // So we train for one step.
            TrainNodes();
        }

        public double Predict(double[] features)
        {
            LoadInputs(features);
            MarkNodesStale();
            // Assume continuous regression of a single output
            return outputNodes[0].Output;
        }


        private void LoadInputs(double[] features)
        {
            for (int i = 0; i < features.Length; i++)
            {
                inputNodes[i].Value = features[i];
            }
        }

        private void MarkNodesStale()
        {
            // Mark each node as dirty/stale
            inputNodes.ForEach(node => node.MarkStale());
            hiddenNodes.ForEach(list => list.ForEach(node => node.MarkStale()));
            outputNodes.ForEach(node => node.MarkStale());
        }

        private void TrainNodes()
        {
            // Tell each of the hidden and output nodes to train one step using whatever the current output values are through the network
            hiddenNodes.ForEach(list => list.ForEach(node => node.Train()));
            outputNodes.ForEach(node => node.Train());
        }

        // Properties used by the nodes to register themselves with the network
        private int nextNodeId = 0;
        public int NextNodeId()
        {
            return nextNodeId++;
        }
    }
}
