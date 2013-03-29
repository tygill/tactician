using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class DominionLearnerTask
    {
        public string Card { get; private set; }
        public IList<string> Features { get; private set; }
        public DominionLearner Learner { get; private set; }
        public double NormalizationMin { get; private set; }
        public double NormalizationMax { get; private set; }
        private string DatabaseFile;

        public DominionLearnerTask(string card, IEnumerable<string> features, string dbFile, double min, double max)
        {
            Card = card;
            NormalizationMin = min;
            NormalizationMax = max;
            Features = new List<string>(features);
            Learner = LearnerFactory.CreateDominionLearner(Card, Features);
            DatabaseFile = dbFile;
        }

        public void RunTask()
        {
            Stopwatch stopwatch = Stopwatch.StartNew();

            using (SQLiteConnection conn = new SQLiteConnection("Data Source=:memory:;Version=3;"))
            {
                conn.Open();

                string sql;

                Console.WriteLine("{0}: Creating memory database", Card);
                // Attach and extract the data from the source database
                sql = @"ATTACH @db AS `source_db`;";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    command.Parameters.AddWithValue("@db", DatabaseFile);
                    command.ExecuteNonQuery();
                }
                Console.WriteLine("{0}: Filling...", Card);
                sql = String.Format(@"CREATE TABLE `main`.`instances` AS SELECT `{0}`,`card_bought`, `player_final_score`, `use`, `randomizer` FROM `source_db`.`instances` WHERE `source_db`.`instances`.`card_bought` = @card_bought;", string.Join("`, `", Features));
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    command.Parameters.AddWithValue("@card_bought", Card);
                    command.ExecuteNonQuery();
                }
                Console.WriteLine("{0}: Indexing...", Card);
                sql = @"CREATE INDEX `main`.`use_index` ON `instances` (`use`);";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    command.ExecuteNonQuery();
                }
                sql = @"DETACH `source_db`;";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    command.ExecuteNonQuery();
                }
                Console.WriteLine("{0}: Memory database complete", Card);


                // Get the total number of instances we have available
                int totalInstances = 0;
                int trainingInstances = 0;
                int validationInstances = 0;
                int testingInstances = 0;
                //sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'training'";
                sql = @"SELECT COUNT(*) FROM `instances` WHERE `use` = 'training'";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    //command.Parameters.AddWithValue("@card_bought", Card);
                    trainingInstances = Convert.ToInt32(command.ExecuteScalar());
                }
                //sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'validation'";
                sql = @"SELECT COUNT(*) FROM `instances` WHERE `use` = 'validation'";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    //command.Parameters.AddWithValue("@card_bought", Card);
                    validationInstances = Convert.ToInt32(command.ExecuteScalar());
                }
                //sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought AND `use` = 'testing'";
                sql = @"SELECT COUNT(*) FROM `instances` WHERE `use` = 'testing'";
                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    //command.Parameters.AddWithValue("@card_bought", Card);
                    testingInstances = Convert.ToInt32(command.ExecuteScalar());
                }
                /*
                sql = @"SELECT COUNT(*) FROM `instances` WHERE `card_bought` = @card_bought";
                using (SQLiteCommand command = new SQLiteCommand(sql, Connection))
                {
                    command.Parameters.AddWithValue("@card_bought", Card);
                    totalInstances = Convert.ToInt32(command.ExecuteScalar());
                }
                //*/
                totalInstances = trainingInstances + validationInstances + testingInstances;
                Console.WriteLine("{0}: {1} Instances ({2} training, {3} validation, {4} testing)", Card, totalInstances, trainingInstances, validationInstances, testingInstances);
                /*
                bool tmp = true;
                if (tmp)
                {
                    return;
                }
                 */

                // Epoch status
                int epochSize = trainingInstances; // Math.Min(trainingInstances, 500);
                int validationEpochSize = validationInstances; // Math.Min(validationInstances, 200);
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
                uint trained = 0;
                bool allTrained = false;
                bool done = false;
                double previousMSE = double.MaxValue;
                //sql = string.Format(@"SELECT `{0}`, `player_final_score` FROM `instances` WHERE `card_bought` = @card_bought AND `use` = @use ORDER BY RANDOM();", string.Join("`, `", Features));
                sql = string.Format(@"SELECT `{0}`, `player_final_score` FROM `instances` WHERE `use` = @use ORDER BY RANDOM();", string.Join("`, `", Features));
                SQLiteDataReader trainingReader = SQLReader(sql, "training", conn); // Bootstrap these
                SQLiteDataReader validationReader = SQLReader(sql, "validation", conn);
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
                                trainingReader = SQLReader(sql, "training", conn);
                            }

                            // Read each feature from our database result
                            for (int i = 0; i < Features.Count; i++)
                            {
                                instance[i] = trainingReader.GetDouble(i);
                            }
                            // The target output is the last column in the row
                            Learner.TrainInstance(instance, Normalize(trainingReader.GetDouble(Features.Count)));
                            trained++;
                        }
                    }

                    // Test the predictive accuracy on the entire validation set
                    //List<double> targets = new List<double>(validationInstances);
                    //List<double> errors = new List<double>(validationInstances);
                    double sse = 0.0;
                    for (int e = 0; e < validationEpochSize; e++)
                    {
                        // If there's nothing left to read, then restart the reader
                        while (!validationReader.Read())
                        {
                            validationReader.Dispose();
                            validationReader = null;
                            // Reuse the same sql currently...
                            validationReader = SQLReader(sql, "validation", conn);
                        }

                        for (int i = 0; i < Features.Count; i++)
                        {
                            instance[i] = validationReader.GetDouble(i);
                        }
                        // The target output is the last column in the row
                        double prediction = Learner.Predict(instance);
                        double target = Normalize(validationReader.GetDouble(Features.Count));
                        double error = target - prediction;
                        sse += error * error;
                        //targets.Add(target);
                        //errors.Add(error);
                        //Console.WriteLine("Prediction: {0} {1} {2}", Math.Round(prediction, 3), Math.Round(target, 3), Math.Round(error, 3));
                    }
                    /*
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
                        Console.WriteLine("Prediction: {0} {1} {2}", Math.Round(prediction, 3), Math.Round(Normalize(reader.GetDouble(Features.Count)), 3), Math.Round(error, 3));
                    });
                     */
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

                    if ((currentAverage >= previousAverage && mse < previousMSE) || currentAverage == previousAverage)
                    {
                        done = true;
                    }

                    previousMSE = mse;

                    epochWatch.Stop();

                    Console.WriteLine("{0}:{1} Training Accuracy (Epoch took {2:00}:{3:00}):\n  SSE: {4}\n  MSE: {5}", Card, epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds, sse, mse);
                    //Console.WriteLine("{0}:{1} Training Accuracy (Epoch took {2:00}:{3:00}. {4} trained, {5} validated):\n  SSE: {6}\n  MSE: {7}", Card, epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds, epochSize, validationEpochSize, sse, mse);

                    //Console.WriteLine("{0}:{6} Training Accuracy:\n    SSE: {7}\n    MSE: {1}\n   RMSE: {2}\n AvgErr: {3}\n StdDev: {4}\n AvgTgt: {5}", Card, mse, Math.Sqrt(mse), errors.Average(), errors.StdDev(), targets.Average(), epochsTrained, errors.Select(x => x * x).Sum());

                    epochsTrained++;
                }
                Console.WriteLine("{0} Training Complete\n Trained on {1} instances over {2} epochs", Card, trained, epochsTrained);
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
            }

            stopwatch.Stop();
            Console.WriteLine("{0} Complete!\n Took {1} minutes, {2} seconds", Card, Math.Floor(stopwatch.Elapsed.TotalMinutes), stopwatch.Elapsed.Seconds);
        }

        public double Normalize(double value)
        {
            // Try normalizing to just raw win/lose value.
            //return value > 0 ? 0.9 : 0.1;
            return (value - NormalizationMin) / (NormalizationMax - NormalizationMin);
            //return value; // No normalization.
        }

        private delegate void ReadRow(SQLiteDataReader reader);

        /*
        private void SQLForEach(string sql, string use, ReadRow rowReader, SQLiteConnection conn)
        {
            using (SQLiteCommand command = new SQLiteCommand(sql, conn))
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
        //*/

        private SQLiteDataReader SQLReader(string sql, string use, SQLiteConnection conn)
        {
            using (SQLiteCommand command = new SQLiteCommand(sql, conn))
            {
                //command.Parameters.AddWithValue("@card_bought", Card);
                command.Parameters.AddWithValue("@use", use);
                return command.ExecuteReader();
            }
        }
    }
}
