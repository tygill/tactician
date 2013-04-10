using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class DominionLearnerTask
    {
        public string Card { get; private set; }
        public IList<string> Features { get; private set; }
        public string OutputFeature { get; private set; }
        public double[] Boosts { get; private set; }
        public bool Boost { get; private set; }
        public double BoostValue { get; private set; }
        public bool SigmoidOutputs { get; private set; }
        public double TrainingPercent { get; private set; }
        public uint? MaxTrainingsPerEpoch { get; private set; }
        public double ValidationPercent { get; private set; }
        public uint? MaxValidationsPerEpoch { get; private set; }
        public uint EpochWinow { get; private set; }
        public uint MaxEpochs { get; private set; }
        public double NormalizationMin { get; private set; }
        public double NormalizationMax { get; private set; }
        private string DatabaseFile;

        public DominionLearnerTask(string card, IList<string> features, string outputFeature, string dbFile, double trainingPercent, double validationPercent, double min, double max, bool boost, bool sigmoidOutputs, uint? maxTrainingsPerEpoch = null, uint? maxValidationsPerEpoch = null, uint epochWindow = 20, uint maxEpochs = uint.MaxValue)
        {
            Card = card;
            OutputFeature = outputFeature;
            SigmoidOutputs = sigmoidOutputs;
            TrainingPercent = trainingPercent;
            MaxTrainingsPerEpoch = maxTrainingsPerEpoch;
            ValidationPercent = validationPercent;
            MaxValidationsPerEpoch = maxValidationsPerEpoch;
            EpochWinow = epochWindow;
            MaxEpochs = maxEpochs;
            NormalizationMin = min;
            NormalizationMax = max;
            // Remove the three ratio features, as they are closely correlated with the regular card type counts?
            Features = features;//.Where(name => !name.Contains("_ratio")).ToList();
            // Prune out some features that we don't want to use
            /*
            Features = features
                .Where(name =>
                    !name.Contains("_in_supply") || name.Contains("_cards_in_supply"))
                .Where(name =>
                    !name.Contains("_in_player_deck") ||
                    name == "already_in_player_deck" ||
                    name ==
                        string.Format("{0}_in_player_deck",
                            Card != "None"
                                ? Dominion.GetCard(Card).Plural.Replace("'", "").Replace(' ', '_').ToLowerInvariant()
                                : "none"))
                .ToList();
            //*/
            DatabaseFile = dbFile;

            // How likely is a particular card in a given game? This will be used to boost features that are only in a specific game.
            double likelihood = 0.0;
            {
                for (int i = 0; i < 10; i++)
                {
                    likelihood += 1.0 / (Dominion.Cards.Count() - i);
                }
            }
            //Console.WriteLine("Likelihood: {0}", likelihood);

            Boost = boost;
            BoostValue = 1.0 / likelihood;
            Boosts = new double[Features.Count];
            {
                for (int i = 0; i < Features.Count; i++)
                {
                    if (Boost)
                    {
                        Boosts[i] = GetFeatureBoost(Features[i]);
                    }
                    else
                    {
                        Boosts[i] = 1.0;
                    }
                }
            }
            //Console.WriteLine("Boosting: {0}", string.Join(",", Boosts));


        }

        private double GetFeatureBoost(string feature)
        {
            if (feature.Contains("_acquired"))
            {
                if (feature != "colonies_acquired" && feature != "duchies_acquired" && feature != "estates_acquired" && feature != "provinces_acquired")
                {
                    return BoostValue;
                }
            }

            // Default return
            return 1.0;
        }

        public TaskResult RunTask()
        {
            Stopwatch stopwatch = Stopwatch.StartNew();

            Console.WriteLine("{0}: Beginning Training", Card);

            TaskResult result = new TaskResult();

            using (DominionLearner Learner = LearnerFactory.CreateDominionLearner(Card, Features, Boosts, SigmoidOutputs))
            {
                Directory.CreateDirectory(Learner.Folder);

                using (StreamWriter log = new StreamWriter(String.Format("{0}\\{1}.txt", Learner.Folder, Card), false))
                {
                    using (SQLiteConnection conn = new SQLiteConnection(@"Data Source=:memory:;Version=3;"))
                    {
                        conn.Open();

                        string sql;

                        // Create an in-memory database to load data from
                        log.WriteLine("{0}: Creating in-memory database", Card);
                        log.Flush();
                        // Attach and extract the data from the source database
                        sql = @"ATTACH @db AS `source_db`;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.Parameters.AddWithValue("@db", DatabaseFile);
                            command.ExecuteNonQuery();
                        }

                        log.WriteLine("{0}: Copying data...", Card);
                        log.Flush();
                        //sql = String.Format(@"CREATE TABLE `main`.`instances` AS SELECT `{0}`,`card_bought`, `player_final_score`, `use`, `randomizer` FROM `source_db`.`instances` WHERE `source_db`.`instances`.`card_bought` = @card_bought;", string.Join("`, `", Features));
                        sql = String.Format(@"CREATE TABLE `main`.`instances` AS SELECT `{0}`,`card_bought`, `{1}`, `game_second` FROM `source_db`.`instances`{2};", string.Join("`, `", Features), OutputFeature, Card != "All" ? " WHERE `source_db`.`instances`.`card_bought` = @card_bought" : "");
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            if (Card != "All")
                            {
                                command.Parameters.AddWithValue("@card_bought", Card);
                            }
                            command.ExecuteNonQuery();
                        }
                        sql = @"DETACH `source_db`;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        log.WriteLine("{0}: Creating index...", Card);
                        log.Flush();
                        //sql = @"CREATE INDEX `main`.`use_index` ON `instances` (`use`);";
                        sql = @"CREATE INDEX `main`.`game_second_index` ON `instances` (`game_second`);";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        log.WriteLine("{0}: Creation of in-memory database complete", Card);
                        log.Flush();


                        // Get the total number of instances we have available
                        result.TotalInstances = 0;
                        result.TrainingInstances = 0;
                        result.ValidationInstances = 0;
                        result.TestingInstances = 0;
                        // Using the second field (0-60) as the set divider gives these splits
                        double trainingCutoff = TrainingPercent * 60;
                        double validationCutoff = ValidationPercent * trainingCutoff;;
                        // [<0> Validation <validationCutof> Training <trainingCutoff> Testing<60>]
                        sql = @"SELECT COUNT(*) FROM `instances` WHERE `game_second` >= @validationCutoff AND `game_second` < @trainingCutoff;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.Parameters.AddWithValue("@trainingCutoff", trainingCutoff);
                            command.Parameters.AddWithValue("@validationCutoff", validationCutoff);
                            result.TrainingInstances = Convert.ToUInt32(command.ExecuteScalar());
                        }
                        sql = @"SELECT COUNT(*) FROM `instances` WHERE `game_second` < @validationCutoff;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.Parameters.AddWithValue("@validationCutoff", validationCutoff);
                            result.ValidationInstances = Convert.ToUInt32(command.ExecuteScalar());
                        }
                        sql = @"SELECT COUNT(*) FROM `instances` WHERE `game_second` >= @trainingCutoff;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.Parameters.AddWithValue("@trainingCutoff", trainingCutoff);
                            result.TestingInstances = Convert.ToUInt32(command.ExecuteScalar());
                        }
                        result.TotalInstances = result.TrainingInstances + result.ValidationInstances + result.TestingInstances;
                        result.TrainingInstances = result.TrainingInstances;
                        result.ValidationInstances = result.ValidationInstances;
                        result.TestingInstances = result.TestingInstances;
                        log.WriteLine("{0}: {1} Instances ({2} training, {3} validation, {4} testing)", Card, result.TotalInstances, result.TrainingInstances, result.ValidationInstances, result.TestingInstances);
                        log.Flush();

                        if (Boost)
                        {
                            log.WriteLine("Using boosting on rare features (boost value: {0})", BoostValue);
                        }

                        log.WriteLine("Using {0} as the target/output feature", OutputFeature);
                        log.Flush();


                        // Epoch status
                        uint trainingsPerEpoch = MaxTrainingsPerEpoch.HasValue ? MaxTrainingsPerEpoch.Value : result.TrainingInstances; // Math.Min(trainingInstances, 500);
                        uint validationsPerEpoch = MaxValidationsPerEpoch.HasValue ? MaxValidationsPerEpoch.Value : result.ValidationInstances; // Math.Min(validationInstances, 200);
                        result.Epochs = 0;

                        // Termination criteria
                        Queue<double> currentErrorWindow = new Queue<double>((int)EpochWinow + 1); // The +1 is so that we can enqueue, check if the size is greater, and then dequeue it rather than checking before enqueuing a new error
                        Queue<double> previousErrorWindow = new Queue<double>((int)EpochWinow + 1);
                        // To make sure the initial average is high, no training happens on the first epoch

                        // Temporary variable
                        double[] instance = new double[Features.Count];

                        // Train the learner
                        result.TotalInstancesTrained = 0;
                        bool allTrained = false;
                        bool done = false;
                        bool averagePassed = false;
                        double previousMSE = double.MaxValue;
                        sql = string.Format(@"SELECT `{0}`, `{1}` FROM `instances` WHERE {{0}} ORDER BY RANDOM();", string.Join("`, `", Features), OutputFeature);
                        using (SQLiteCommand trainingCommand = new SQLiteCommand(string.Format(sql, "`game_second` >= @validationCutoff AND `game_second` < @trainingCutoff"), conn))
                        using (SQLiteCommand validationCommand = new SQLiteCommand(string.Format(sql, "`game_second` < @validationCutoff"), conn))
                        using (SQLiteCommand testingCommand = new SQLiteCommand(string.Format(sql, "`game_second` >= @trainingCutoff"), conn))
                        {
                            // Setup parameters
                            trainingCommand.Parameters.AddWithValue("@trainingCutoff", trainingCutoff);
                            trainingCommand.Parameters.AddWithValue("@validationCutoff", validationCutoff);
                            validationCommand.Parameters.AddWithValue("@validationCutoff", validationCutoff);
                            testingCommand.Parameters.AddWithValue("@trainingCutoff", trainingCutoff);

                            SQLiteDataReader trainingReader = trainingCommand.ExecuteReader(); // Bootstrap these
                            SQLiteDataReader validationReader = validationCommand.ExecuteReader();
                            Stopwatch epochWatch = new Stopwatch();
                            while (!(done && allTrained))
                            {
                                epochWatch.Restart();

                                // Train one round
                                // Don't train on the first epoch, so the initial random error can be compared
                                if (result.Epochs != 0)
                                {
                                    for (int e = 0; e < trainingsPerEpoch; e++)
                                    {
                                        // If there's nothing left to read, then restart the reader
                                        while (!trainingReader.Read())
                                        {
                                            trainingReader.Dispose();
                                            allTrained = true; // All training instances have been used at least once
                                            trainingReader = null;
                                            trainingReader = trainingCommand.ExecuteReader();
                                        }

                                        // Read each feature from our database result
                                        for (int i = 0; i < Features.Count; i++)
                                        {
                                            instance[i] = trainingReader.GetDouble(i);
                                        }
                                        // The target output is the last column in the row
                                        Learner.TrainInstance(instance, Normalize(trainingReader.GetDouble(Features.Count)));
                                        result.TotalInstancesTrained++;
                                    }
                                }


                                // Test the predictive accuracy on the entire validation set
                                double sse = 0.0;
                                for (int e = 0; e < validationsPerEpoch; e++)
                                {
                                    // If there's nothing left to read, then restart the reader
                                    while (!validationReader.Read())
                                    {
                                        validationReader.Dispose();
                                        validationReader = null;
                                        validationReader = validationCommand.ExecuteReader();
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
                                    if (result.Epochs > 0)
                                    {
                                        //Console.WriteLine(" Instance:\n  {0}", string.Join("\n  ", Features.Zip(instance, (feature, value) => new Tuple<string, double>(feature, value))));
                                        //Console.WriteLine(" Prediction: {0,3} Expected {1,3} Error {2,3}", Math.Round(UnNormalize(prediction)), Math.Round(UnNormalize(target)), Math.Round(UnNormalize(target) - UnNormalize(prediction)));
                                        //log.WriteLine(" Prediction: {0,3} Expected {1,3} Error {2,3}", Math.Round(UnNormalize(prediction)), Math.Round(UnNormalize(target)), Math.Round(UnNormalize(target) - UnNormalize(prediction)));
                                    }
                                }
                                double mse = sse / validationsPerEpoch;


                                // Check for termination
                                currentErrorWindow.Enqueue(mse);
                                if (currentErrorWindow.Count > EpochWinow)
                                {
                                    double oldMse = currentErrorWindow.Dequeue();
                                    previousErrorWindow.Enqueue(oldMse);
                                    if (previousErrorWindow.Count > EpochWinow)
                                    {
                                        previousErrorWindow.Dequeue();
                                    }
                                }

                                double currentAverage = currentErrorWindow.Average();
                                double previousAverage = previousErrorWindow.Count() > 0 ? previousErrorWindow.Average() : double.MaxValue;

                                if (currentAverage >= previousAverage)
                                {
                                    averagePassed = true;
                                }

                                if ((averagePassed && mse < previousMSE) || currentAverage == previousAverage)
                                {
                                    done = true;
                                }

                                if (result.Epochs >= MaxEpochs)
                                {
                                    done = true;
                                }

                                previousMSE = mse;


                                // This epoch has completed
                                epochWatch.Stop();
                                //Console.WriteLine("{0}:{1} Training Accuracy (Epoch took {2:00}:{3:00}):\n  SSE: {4}\n  MSE: {5}", Card, epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds, sse, mse);

                                //*
                                // Test the predictive accuracy on the each data set
                                //double trainingSSE = CalculateSSE(trainingCommand, Learner, instance);
                                //double trainingMSE = trainingSSE / trainingInstances;
                                //double validationSSE = CalculateSSE(validationCommand, Learner, instance);
                                //double validationMSE = validationSSE / validationInstances;
                                double validationSSE = sse;
                                double validationMSE = mse;
                                //double testingSSE = CalculateSSE(testingCommand, Learner, instance);
                                //double testingMSE = testingSSE / testingInstances;

                                log.WriteLine("{0} Epoch Status", Card);
                                log.WriteLine(" Epoch {0} completed in {1:00}:{2:00}", result.Epochs, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds);
                                log.WriteLine(" Trained on {0} instances total", result.TotalInstancesTrained);
                                //log.WriteLine(" SSE (training set):   {0:.0000000000} ({1:.0000000000})", trainingSSE, UnNormalize(Math.Sqrt(trainingSSE)));
                                //log.WriteLine(" SSE (validation set): {0:.0000000000} ({1:.0000000000})", validationSSE, UnNormalize(Math.Sqrt(validationSSE)));
                                //log.WriteLine(" SSE (testing set):    {0:.0000000000} ({1:.0000000000})", testingSSE, UnNormalize(Math.Sqrt(testingSSE)));
                                //log.WriteLine(" MSE (training set):   {0:.0000000000} ({1:.0000000000})", trainingMSE, UnNormalize(Math.Sqrt(trainingMSE)));
                                log.WriteLine(" MSE (validation set): {0:.0000000000} ({1:.0000000000})", validationMSE, UnNormalize(Math.Sqrt(validationMSE)));
                                //log.WriteLine(" MSE (testing set):    {0:.0000000000} ({1:.0000000000})", testingMSE, UnNormalize(Math.Sqrt(testingMSE)));
                                log.Flush();
                                //*/


                                //Console.WriteLine("{0} Epoch Status", Card);
                                //Console.WriteLine(" Epoch {0} completed in {1:00}:{2:00}", epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds);
                                //Console.WriteLine(" Trained on {0} instances total", totalTrained);
                                //Console.WriteLine(" SSE (training set):   {0:.0000000000} ({1:.0000000000})", trainingSSE, UnNormalize(Math.Sqrt(trainingSSE)));
                                //Console.WriteLine(" SSE (validation set): {0:.0000000000} ({1:.0000000000})", validationSSE, UnNormalize(Math.Sqrt(validationSSE)));
                                //Console.WriteLine(" SSE (testing set):    {0:.0000000000} ({1:.0000000000})", testingSSE, UnNormalize(Math.Sqrt(testingSSE)));
                                //Console.WriteLine(" MSE (training set):   {0:.0000000000} ({1:.0000000000})", trainingMSE, UnNormalize(Math.Sqrt(trainingMSE)));
                                Console.WriteLine(" MSE (validation set): {0:.0000000000} ({1:.0000000000})", validationMSE, UnNormalize(Math.Sqrt(validationMSE)));
                                //Console.WriteLine(" MSE (testing set):    {0:.0000000000} ({1:.0000000000})", testingMSE, UnNormalize(Math.Sqrt(testingMSE)));

                                //Console.WriteLine("{0}:{1} Training Accuracy (Epoch took {2:00}:{3:00}. {4} trained, {5} validated):\n  SSE: {6}\n  MSE: {7}", Card, epochsTrained, Math.Floor(epochWatch.Elapsed.TotalMinutes), epochWatch.Elapsed.Seconds, epochSize, validationEpochSize, sse, mse);
                                //Console.WriteLine("{0}:{6} Training Accuracy:\n    SSE: {7}\n    MSE: {1}\n   RMSE: {2}\n AvgErr: {3}\n StdDev: {4}\n AvgTgt: {5}", Card, mse, Math.Sqrt(mse), errors.Average(), errors.StdDev(), targets.Average(), epochsTrained, errors.Select(x => x * x).Sum());

                                result.Epochs++;
                            }
                            trainingReader.Dispose();
                            trainingReader = null;
                            validationReader.Dispose();
                            validationReader = null;

                            currentErrorWindow.Clear();
                            currentErrorWindow = null;
                            previousErrorWindow.Clear();
                            previousErrorWindow = null;
                        }

                        sql = string.Format(@"SELECT `{0}`, `{1}` FROM `instances` WHERE {{0}};", string.Join("`, `", Features), OutputFeature);
                        using (SQLiteCommand trainingCommand = new SQLiteCommand(string.Format(sql, "`game_second` >= @validationCutoff AND `game_second` < @trainingCutoff"), conn))
                        using (SQLiteCommand validationCommand = new SQLiteCommand(string.Format(sql, "`game_second` < @validationCutoff"), conn))
                        using (SQLiteCommand testingCommand = new SQLiteCommand(string.Format(sql, "`game_second` >= @trainingCutoff"), conn))
                        {
                            // Report all the errors
                            {
                                // Test the predictive accuracy on the each data set
                                result.TrainingSSE = CalculateSSE(trainingCommand, Learner, instance);
                                result.TrainingMSE = result.TrainingSSE / result.TrainingInstances;
                                double trainingAccuracy = CalculatePredictionAccuracy(trainingCommand, Learner, instance);
                                result.ValidationSSE = CalculateSSE(validationCommand, Learner, instance);
                                result.ValidationMSE = result.ValidationSSE / result.ValidationInstances;
                                double validationAccuracy = CalculatePredictionAccuracy(validationCommand, Learner, instance);
                                result.TestingSSE = CalculateSSE(testingCommand, Learner, instance);
                                result.TestingMSE = result.TestingSSE / result.TestingInstances;
                                double testingAccuracy = CalculatePredictionAccuracy(testingCommand, Learner, instance);

                                //Console.WriteLine("{0} Training Complete\n Trained on {1} instances over {2} epochs", Card, totalTrained, epochsTrained);
                                Console.WriteLine("  {0} Trained (MSE: {1:.000} Training, {2:.000} Validation, {3:.000} Testing)", Card, Math.Round(result.TrainingMSE, 3), Math.Round(result.ValidationMSE, 3), Math.Round(result.TestingMSE, 3));
                                Console.WriteLine("  {0} Trained (Mean Score Error: {1:.000} Training, {2:.000} Validation, {3:.000} Testing)", Card, Math.Round(UnNormalize(Math.Sqrt(result.TrainingMSE)), 3), Math.Round(UnNormalize(Math.Sqrt(result.ValidationMSE)), 3), Math.Round(UnNormalize(Math.Sqrt(result.TestingMSE)), 3));
                                log.WriteLine("{0} Training Complete", Card);
                                log.WriteLine(" Trained on {0} instances over {1} epochs", result.TotalInstancesTrained, result.Epochs);
                                log.WriteLine(" SSE (training set):   {0:.0000000000} ({1:.0000000000})", result.TrainingSSE, UnNormalize(Math.Sqrt(result.TrainingSSE)));
                                log.WriteLine(" SSE (validation set): {0:.0000000000} ({1:.0000000000})", result.ValidationSSE, UnNormalize(Math.Sqrt(result.ValidationSSE)));
                                log.WriteLine(" SSE (testing set):    {0:.0000000000} ({1:.0000000000})", result.TestingSSE, UnNormalize(Math.Sqrt(result.TestingSSE)));
                                log.WriteLine(" MSE (training set):   {0:.0000000000} ({1:.0000000000})", result.TrainingMSE, UnNormalize(Math.Sqrt(result.TrainingMSE)));
                                log.WriteLine(" MSE (validation set): {0:.0000000000} ({1:.0000000000})", result.ValidationMSE, UnNormalize(Math.Sqrt(result.ValidationMSE)));
                                log.WriteLine(" MSE (testing set):    {0:.0000000000} ({1:.0000000000})", result.TestingMSE, UnNormalize(Math.Sqrt(result.TestingMSE)));
                                log.WriteLine(" PA (training set):   {0:.000}", Math.Round(trainingAccuracy, 3));
                                log.WriteLine(" PA (validation set): {0:.000})", Math.Round(validationAccuracy, 3));
                                log.WriteLine(" PA (testing set):    {0:.000})", Math.Round(testingAccuracy, 3));
                            }
                        }
                    }

                    using (StreamWriter file = new StreamWriter(String.Format("{0}\\{1}.json", Learner.Folder, Card), false))
                    {
                        file.Write(Learner.Serialize());
                    }

                    stopwatch.Stop();
                    //Console.WriteLine("{0} Complete!\n Took {1} minutes, {2} seconds", Card, Math.Floor(stopwatch.Elapsed.TotalMinutes), stopwatch.Elapsed.Seconds);
                    Console.WriteLine(" {0}: Complete! (Took {1} minutes, {2} seconds)", Card, Math.Floor(stopwatch.Elapsed.TotalMinutes), stopwatch.Elapsed.Seconds);
                    log.WriteLine("{0} Complete!", Card);
                    log.WriteLine(" Took {0} minutes, {1} seconds", Math.Floor(stopwatch.Elapsed.TotalMinutes), stopwatch.Elapsed.Seconds);
                }
            }

            return result;
        }

        public double Normalize(double value)
        {
            return (value - NormalizationMin) / (NormalizationMax - NormalizationMin);
        }

        public double UnNormalize(double value)
        {
            return (value * (NormalizationMax - NormalizationMin)) + NormalizationMin;
        }

        public double CalculateSSE(SQLiteCommand command, DominionLearner learner, double[] instance)
        {
            using (SQLiteDataReader reader = command.ExecuteReader())
            {
                double sse = 0.0;
                while (reader.Read())
                {
                    for (int i = 0; i < Features.Count; i++)
                    {
                        instance[i] = reader.GetDouble(i);
                    }
                    // The target output is the last column in the row
                    double prediction = learner.Predict(instance);
                    double target = Normalize(reader.GetDouble(Features.Count));
                    double error = target - prediction;
                    sse += error * error;
                }
                return sse;
            }
        }

        public double CalculatePredictionAccuracy(SQLiteCommand command, DominionLearner learner, double[] instance)
        {
            using (SQLiteDataReader reader = command.ExecuteReader())
            {
                int sum = 0;
                int count = 0;
                while (reader.Read())
                {
                    for (int i = 0; i < Features.Count; i++)
                    {
                        instance[i] = reader.GetDouble(i);
                    }
                    // The target output is the last column in the row
                    double prediction = learner.Predict(instance);
                    if(prediction > .5)
                    {
                        prediction = 1;
                    }
                    else
                    {
                        prediction = 0;
                    }
                    double target = Normalize(reader.GetDouble(Features.Count));
                    if (prediction == target)
                    {
                        sum++;
                    }
                    count++;
                }
                return (double)sum/count;
            }
        }

    }
}
