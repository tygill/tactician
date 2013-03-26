using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class DominionLearnerTask : IDisposable
    {
        public string Card { get; private set; }
        public IList<string> Features { get; private set; }
        public DominionLearner Learner { get; private set; }
        public double NormalizationMin { get; private set; }
        public double NormalizationMax { get; private set; }
        private SQLiteConnection Connection;

        public DominionLearnerTask(string card, IEnumerable<string> features, SQLiteConnection conn, double min, double max)
        {
            Card = card;
            NormalizationMin = min;
            NormalizationMax = max;
            Features = new List<string>(features);
            Learner = LearnerFactory.CreateDominionLearner(Card, Features);
            Connection = (SQLiteConnection)conn.Clone();
        }

        public void RunTask()
        {
            Stopwatch stopwatch = Stopwatch.StartNew();

            string sql;

            // Get the total number of instances we have available
            int totalInstances = 0;
            int trainingInstances = 0;
            int validationInstances = 0;
            int testingInstances = 0;
            sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought";
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                totalInstances = Convert.ToInt32(command.ExecuteScalar());
            }
            sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'training'";
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                trainingInstances = Convert.ToInt32(command.ExecuteScalar());
            }
            sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'validation'";
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                validationInstances = Convert.ToInt32(command.ExecuteScalar());
            }
            sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'testing'";
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                testingInstances = Convert.ToInt32(command.ExecuteScalar());
            }
            Console.WriteLine("{0}: {1} Instances ({2} training, {3} validation, {4} testing)", Card, totalInstances, trainingInstances, validationInstances, testingInstances);

            // Epoch status
            int epochSize = 500;// Math.Min(validationInstances, 500);
            int epochsTrained = 0;

            // Termination criteria
            int terminationWindowSize = 5; // Epochs to consider for completion
            Queue<double> currentErrorWindow = new Queue<double>(terminationWindowSize + 1); // The +1 is so that we can enqueue, check if the size is greater, and then dequeue it rather than checking before enqueuing a new error
            Queue<double> previousErrorWindow = new Queue<double>(terminationWindowSize + 1);
            // Make sure the initial average is high
            currentErrorWindow.Enqueue(double.MaxValue);
            previousErrorWindow.Enqueue(double.MaxValue);

            // Temporary variable
            double[] instance = new double[Features.Count];

            // Train the learner
            bool allTrained = false;
            bool done = false;
            sql = string.Format(@"SELECT `{0}`, `player_final_score` FROM `instances` WHERE `card_bought` = @card_bought AND `use` = @use ORDER BY RANDOM();", string.Join("`, `", Features));
            SQLiteDataReader trainingReader = SQLReader(sql, "training"); // Bootstrap this
            Stopwatch epochWatch = new Stopwatch();
            while (!(done && allTrained))
            {
                epochWatch.Restart();

                // Don't train on the first epoch
                if (epochsTrained != 0)
                {
                    for (int e = 0; e < epochSize; e++)
                    {
                        // If there's nothing left to read, then restart the reader
                        while (!trainingReader.Read())
                        {
                            trainingReader.Dispose();
                            allTrained = true; // All training instances have been used at least once
                            trainingReader = null;
                            trainingReader = SQLReader(sql, "training");
                        }

                        // Read each feature from our database result
                        for (int i = 0; i < Features.Count; i++)
                        {
                            instance[i] = trainingReader.GetDouble(i);
                        }
                        // The target output is the last column in the row
                        Learner.TrainInstance(instance, Normalize(trainingReader.GetDouble(Features.Count)));
                    }
                }

                // Test the predictive accuracy on the entire validation set
                //List<double> targets = new List<double>(validationInstances);
                //List<double> errors = new List<double>(validationInstances);
                double sse = 0.0;
                // Reuse the same sql currently...
                SQLForEach(sql, "validation", reader =>
                {
                    for (int i = 0; i < Features.Count; i++)
                    {
                        instance[i] = reader.GetDouble(i);
                    }
                    // The target output is the last column in the row
                    double prediction = Learner.Predict(instance);
                    double target = Normalize(reader.GetDouble(Features.Count));
                    double error = target - prediction;
                    sse += error * error;
                    //targets.Add(target);
                    //errors.Add(error);
                    //Console.WriteLine("Prediction: {0} {1} {2}", Math.Round(prediction, 3), Math.Round(Normalize(reader.GetDouble(Features.Count)), 3), Math.Round(error, 3));
                });
                double mse = sse / validationInstances;

                currentErrorWindow.Enqueue(mse);
                if (currentErrorWindow.Count > terminationWindowSize)
                {
                    double oldMse = currentErrorWindow.Dequeue();
                    previousErrorWindow.Enqueue(oldMse);
                    if (previousErrorWindow.Count > terminationWindowSize)
                    {
                        previousErrorWindow.Dequeue();
                    }
                }

                double currentAverage = currentErrorWindow.Average();
                double previousAverage = previousErrorWindow.Average();

                if (currentAverage >= previousAverage)
                {
                    done = true;
                }

                epochWatch.Stop();

                Console.WriteLine("{0}:{1} Training Accuracy (Epoch took {2:00}:{3:00}):\n    SSE: {4}\n    MSE: {5}", Card, epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds, sse, mse);
                //Console.WriteLine("{0}:{6} Training Accuracy:\n    SSE: {7}\n    MSE: {1}\n   RMSE: {2}\n AvgErr: {3}\n StdDev: {4}\n AvgTgt: {5}", Card, mse, Math.Sqrt(mse), errors.Average(), errors.StdDev(), targets.Average(), epochsTrained, errors.Select(x => x * x).Sum());

                epochsTrained++;
            }
            Console.WriteLine("{0} Training Complete", Card);
            //Console.WriteLine("{0} Training Accuracy:\n    MSE: {1}\n   RMSE: {2}\n AvgErr: {3}\n StdDev: {4}\n AvgTgt: {5}\n   Inst: {6}", Card, mse, Math.Sqrt(mse), errors.Average(), errors.StdDev(), targets.Average(), totalInstances);

            /*
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                command.Parameters.AddWithValue("@limit", trainingInstances);
                command.Parameters.AddWithValue("@offset", 0);

                using (SQLiteDataReader reader = command.ExecuteReader())
                {
                    double[] instance = new double[Features.Count];
                    while (reader.Read())
                    {
                        for (int i = 0; i < Features.Count; i++)
                        {
                            instance[i] = reader.GetDouble(i);
                        }
                        // The target output is the last column in the row
                        Learner.TrainInstance(instance, reader.GetDouble(Features.Count));
                    }
                    instance = null;
                }
                Console.WriteLine("{0} Training Complete", Card);
            }
             */
            /*
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                using (SQLiteDataReader reader = command.ExecuteReader())
                {
                    double[] instance = new double[Features.Count];
                    List<double> targets = new List<double>(totalInstances);
                    List<double> errors = new List<double>(totalInstances);
                    double sse = 0.0;
                    while (reader.Read())
                    {
                        for (int i = 0; i < Features.Count; i++)
                        {
                            instance[i] = reader.GetDouble(i);
                        }
                        // The target output is the last column in the row
                        double prediction = Learner.Predict(instance);
                        double error = reader.GetDouble(Features.Count) - prediction;
                        sse += error * error;
                        targets.Add(reader.GetDouble(Features.Count));
                        errors.Add(error);
                    }
                    double mse = sse / totalInstances;
                    Console.WriteLine("{0} Training Accuracy:\n    MSE: {1}\n   RMSE: {2}\n AvgErr: {3}\n StdDev: {4}\n AvgTgt: {5}\n   Inst: {6}", Card, mse, Math.Sqrt(mse), errors.Average(), errors.StdDev(), targets.Average(), totalInstances);
                    instance = null;
                }
            }
             */

            stopwatch.Stop();
            Console.WriteLine("{0} Complete!\n Took {1} minutes, {2} seconds", Card, Math.Floor(stopwatch.Elapsed.TotalMinutes), stopwatch.Elapsed.Seconds);
        }

        public double Normalize(double value)
        {
            // Try normalizing to just raw win/lose value.
            //return value > 0 ? 0.9 : 0.1;
            return (value - NormalizationMin) / (NormalizationMax - NormalizationMin);
        }

        private delegate void ReadRow(SQLiteDataReader reader);

        private void SQLForEach(string sql, string use, ReadRow rowReader)
        {
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                command.Parameters.AddWithValue("@use", use);
                using (SQLiteDataReader reader = command.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        rowReader(reader);
                    }
                }
            }
        }

        private SQLiteDataReader SQLReader(string sql, string use)
        {
            using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
            {
                command.Parameters.AddWithValue("@card_bought", Card);
                command.Parameters.AddWithValue("@use", use);
                return command.ExecuteReader();
            }
        }

        public void Dispose()
        {
            Connection.Dispose();
        }
    }
}
