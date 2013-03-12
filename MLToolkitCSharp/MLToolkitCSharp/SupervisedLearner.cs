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
    public abstract class SupervisedLearner
    {
	    // Before you call this method, you need to divide your data
	    // into a feature matrix and a label matrix.
	    public abstract void train(Matrix features, Matrix labels);

	    // A feature vector goes in. A label vector comes out. (Some supervised
	    // learning algorithms only support one-dimensional label vectors. Some
	    // support multi-dimensional label vectors.)
	    public abstract void predict(double[] features, double[] labels);

	    // The model must be trained before you call this method. If the label is nominal,
	    // it returns the predictive accuracy. If the label is continuous, it returns
	    // the root mean squared error (RMSE). If confusion is non-NULL, and the
	    // output label is nominal, then confusion will hold stats for a confusion matrix.
	    public double measureAccuracy(Matrix features, Matrix labels, Matrix confusion)
	    {
            if (features.rows() != labels.rows())
            {
                throw (new Exception("Expected the features and labels to have the same number of rows"));
            }
            if (labels.cols() != 1)
            {
                throw (new Exception("Sorry, this method currently only supports one-dimensional labels"));
            }
            if (features.rows() == 0)
            {
                throw (new Exception("Expected at least one row"));
            }

		    int labelValues = labels.valueCount(0);
		    if (labelValues == 0) // If the label is continuous...
		    {
			    // The label is continuous, so measure root mean squared error
			    double[] pred = new double[1];
			    double sse = 0.0;
			    for(int i = 0; i < features.rows(); i++)
			    {
				    double[] feat = features.row(i);
				    double[] targ = labels.row(i);
				    pred[0] = 0.0; // make sure the prediction is not biased by a previous prediction
				    predict(feat, pred);
				    double delta = targ[0] - pred[0];
				    sse += (delta * delta);
			    }
			    return Math.Sqrt(sse / features.rows());
		    }
		    else
		    {
			    // The label is nominal, so measure predictive accuracy
			    if (confusion != null)
			    {
				    confusion.setSize(labelValues, labelValues);
				    for(int i = 0; i < labelValues; i++)
					    confusion.setAttrName(i, labels.attrValue(0, i));
			    }
			    int correctCount = 0;
			    double[] prediction = new double[1];
			    for (int i = 0; i < features.rows(); i++)
			    {
				    double[] feat = features.row(i);
				    int targ = (int)labels.get(i, 0);
                    if (targ >= labelValues)
                    {
                        throw new Exception("The label is out of range");
                    }
				    predict(feat, prediction);
				    int pred = (int)prediction[0];
                    if (confusion != null)
                    {
                        confusion.set(targ, pred, confusion.get(targ, pred) + 1);
                    }
                    if (pred == targ)
                    {
                        correctCount++;
                    }
			    }
			    return (double)correctCount / features.rows();
		    }
	    }
    }
}
