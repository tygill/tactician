using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public abstract class BackpropNode : IDisposable
    {
        public BackpropNetwork Network { get; private set; }
        //public static Random Rand = new Random();
        public double LearningRate { get { return Network.LearningRate; } }
        public double SpeedUp { get { return Network.SpeedUp; } }

        public int Id { get; private set; }

        // This stores the connections and weights
        protected IDictionary<BackpropNode, int> inputIndexes = new Dictionary<BackpropNode, int>();
        protected IList<double> weights = new List<double>();
        protected IList<BackpropNode> outputs = new List<BackpropNode>();

        protected bool outputDirty = true;
        protected bool errorDirty = true;

        public BackpropNode(BackpropNetwork network)
        {
            Id = network.NextNodeId();
            Network = network;
        }

        public void Connect(BackpropNode node)
        {
            // Make  up a new small weight
            double weight = ((Network.Rand.NextDouble() * 2.0) - 1.0) * Network.MaxInitialWeight;
            inputIndexes.Add(node, weights.Count); // weights.Count is the index the weight will have on the list
            weights.Add(weight);
            node.outputs.Add(this);
        }

        public virtual void Train() { }

        public double GetWeightFromNode(BackpropNode node)
        {
            return weights[inputIndexes[node]];
        }

        public void MarkStale()
        {
            outputDirty = true;
            errorDirty = true;
        }

        protected static double convertNetToSigmoidOutput(double net)
        {
            return 1.0 / (1.0 + Math.Exp(-net));
        }

        public abstract double Output { get; }

        public abstract double Error { get; }

        public virtual void Serialize(StringBuilder builder)
        {
            builder.Append("{\"id\":");
            builder.Append(Id);
            builder.Append("}");
        }

        public void Dispose()
        {
            inputIndexes.Clear();
            inputIndexes = null;
            weights.Clear();
            weights = null;
            outputs.Clear();
            outputs = null;
        }
    }

    public class HiddenNode : BackpropNode
    {
        public HiddenNode(BackpropNetwork network)
            : base(network)
        {
            // Connect to a bias node
            Connect(Network.BiasNode);
            //Console.WriteLine("HiddenNode: {0}", Id);
        }

        protected double output;
        protected double error;
        protected double previousDelta = 0.0;

        public virtual double FNet()
        {
            // Take the dot product of the inputs and their weights
            double net = inputIndexes.Select(pair => pair.Key.Output * weights[pair.Value]).Sum();
            return convertNetToSigmoidOutput(net);
        }

        public virtual double FNetPrime()
        {
            return Output * (1.0 - Output);
        }

        public override void Train()
        {
            //Console.WriteLine("Training: {0}", Id);
            // Now that the new output is calculated, update the weights so that next time is better
            foreach (KeyValuePair<BackpropNode, int> pair in inputIndexes)
            {
                double delta = LearningRate * pair.Key.Output * Error;
                weights[pair.Value] += delta + SpeedUp * previousDelta; // SpeedUp * previousDelta is our momentum
                previousDelta = delta;
                //Console.WriteLine("{0}->{1} Weight: {2} Delta: {3}", pair.Key.Id, Id, weights[pair.Value], delta);
            }
        }

        public override double Output
        {
            get
            {
                if (outputDirty)
                {
                    // Now we update the output before updating the weights.
                    // This has the same effect as storing all weight updates until after processing for all nodes,
                    // but doesn't require them to be revisted afterwards, and removes the pesky problem of storing all the deltas.
                    output = FNet();
                    // Mark the output as being updated, so that accesses of this property while updating weights don't enter this update again
                    outputDirty = false;
                    //Console.WriteLine(string.Format("{0}: New output: {1}", Id, output));
                }
                return output;
            }
        }

        public override double Error
        {
            get
            {
                if (errorDirty)
                {
                    error = outputs.Select(node => node.Error * node.GetWeightFromNode(this)).Sum() * FNetPrime();
                    errorDirty = false;
                }
                return error;
            }
        }
        
        public override void Serialize(StringBuilder builder)
        {
            builder.Append("{\"id\":");
            builder.Append(Id);
            builder.Append(",\"weights\":{");
            builder.Append(string.Join(",", inputIndexes.Select(pair => string.Format("\"{0}\":{1}", pair.Key.Id, weights[pair.Value]))));
            builder.Append("}}");
        }
    }

    public class OutputNode : HiddenNode
    {
        public double Target { get; set; }

        public OutputNode(BackpropNetwork network)
            : base(network)
        {
            // The HiddenNode constructor will handle connecting to the BiasNode
            //Console.WriteLine("OutputNode: {0}", Id);
        }

        public override double FNet()
        {
            // Take the dot product of the inputs and their weights
            return inputIndexes.Select(pair => pair.Key.Output * weights[pair.Value]).Sum();
        }

        public override double FNetPrime()
        {
            return 1.0;
        }

        // This is overriden to disable the sigmoid conversion of net to output
        /*
        public override double Output
        {
            get
            {
                if (outputDirty)
                {
                    // Take the dot product of the inputs and their weights
                    //double net = inputIndexes.Select(pair => pair.Key.Output * weights[pair.Value]).Sum();
                    // Now we update the output before updating the weights.
                    // This has the same effect as storing all weight updates until after processing for all nodes,
                    // but doesn't require them to be revisted afterwards, and removes the pesky problem of storing all the deltas.
                    output = FNet();
                    // Mark the output as being updated, so that accesses of this property while updating weights don't enter this update again
                    outputDirty = false;
                    //Console.WriteLine(string.Format("{0}: New output: {1}", Id, output));
                }
                return output;
            }
        }
        //*/

        public override double Error
        {
            get
            {
                if (errorDirty)
                {
                    error = (Target - Output) * FNetPrime();// *Output * (1.0 - Output);
                    errorDirty = false;
                }
                return error;
            }
        }

        public override void Serialize(StringBuilder builder)
        {
            builder.Append("{\"id\":");
            builder.Append(Id);
            builder.Append(",\"weights\":{");
            builder.Append(string.Join(",", inputIndexes.Select(pair => string.Format("\"{0}\":{1}", pair.Key.Id, weights[pair.Value]))));
            builder.Append("}}");
        }
    }

    public class InputNode : BackpropNode
    {
        public string Label { get; private set; }

        public InputNode(BackpropNetwork network, string label)
            : base(network)
        {
            //Console.WriteLine("InputNode: {0}", Id);
            Label = label;
        }

        private double value;
        public double Value
        {
            get { return value; }
            set
            {
                this.value = value;
                //Console.WriteLine(string.Format("{0}: New input/output: {1}", Id, this.value));
            }
        }

        public override double Output { get { return Value; } }

        public override double Error { get { return 0.0; } }

        public override void Serialize(StringBuilder builder)
        {
            builder.Append("{\"id\":");
            builder.Append(Id);
            builder.Append(",\"label\":\"");
            builder.Append(Label);
            builder.Append("\"}");
        }
    }

    public class BiasNode : BackpropNode
    {
        public BiasNode(BackpropNetwork network)
            : base(network)
        {
            //Console.WriteLine("BiasNode: {0}", Id);
        }

        public override double Output { get { return 1.0; } }

        public override double Error { get { throw new NotImplementedException(); } }
    }
}
