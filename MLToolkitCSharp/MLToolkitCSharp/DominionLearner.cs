using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{


public class DominionLearner:SupervisedLearner {

	public DominionLearner(Random rand){
		this.rand = rand;
	}
	
	public override void train(Matrix features, Matrix labels){
		
		Dictionary<double, Matrix> splitFeatures = new Dictionary<Double, Matrix>();
		Dictionary<double, Matrix> splitLabels = new Dictionary<Double, Matrix>();
		int cardColumn = features.cols() - 1;
		
		// split up the data by the card that was picked for each instance
		for(int instance = 0; instance < features.rows(); instance++){
			double cardPicked = features.get(instance, cardColumn);
			
			// if there isn't already a Matrix corresponding to that card, add one
            if (!splitFeatures.ContainsKey(cardPicked))
            {
                splitFeatures.Add(cardPicked, new Matrix(features, instance, 0, 1, cardColumn));
                splitLabels.Add(cardPicked, new Matrix(features, instance, 0, 1, labels.cols()));
            }
            else
            {
                // put the instance in the correct matrices
                splitFeatures[cardPicked].add(features, instance, 0, 1);
                splitLabels[cardPicked].add(features, instance, 0, 1);
            }
		}
		
		// add the models for each card type and train on them
		learners = new Dictionary<Double, SupervisedLearner>();
		int totalCards = features.valueCount(features.cols()-1);
		for(double card = 0; card < totalCards; card++){
            Console.WriteLine("Card Num: " + card);
            if (splitFeatures.ContainsKey(card))
            {
                SupervisedLearner cardLearner = new PerceptronLearner(.1, rand, null);
			    learners.Add(card, cardLearner);
			    learners[card].train(splitFeatures[card], splitLabels[card]);
            }
		}

        trainingFeatures = features;
	}

	public override void predict(double[] features, double[] labels){
        double bestPrediction = 0;
        int bestPredictionIndex = 0;
		int numPossibleCards = trainingFeatures.valueCount(trainingFeatures.cols()-1);
		for(int curCard = 0; curCard < numPossibleCards; curCard++)
        {
            if(features[curCard] == 1) // basically if this card is included in the game, then we make a prediction
            {
                if (learners.ContainsKey(curCard))
                {
                    learners[curCard].predict(features, labels);
                }
                if (labels[0] > bestPrediction)
                {
                    bestPrediction = labels[0];
                    bestPredictionIndex = curCard;
                }
            }
		}
        labels[0] = bestPredictionIndex;
	}

	Dictionary<double, SupervisedLearner> learners;
	Matrix trainingFeatures;
	Random rand;
	
}

}
