using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DominionML_SQL
{
    public class DominionML
    {
        public static void Main(string[] args)
        {
            // Parse command line arguments
            List<string> argList = args.ToList<string>();
            string file = args.Contains("-f") ? args[argList.IndexOf("-f") + 1] : "test.db3";
            double trainingPercent = args.Contains("-t") ? double.Parse(args[argList.IndexOf("-t") + 1]) : 0.8;
            uint? maxTrainings = args.Contains("-mt") ? (uint?)uint.Parse(args[argList.IndexOf("-mt") + 1]) : null;
            double validationPercent = args.Contains("-v") ? double.Parse(args[argList.IndexOf("-v") + 1]) : 0.2;
            uint? maxValidations = args.Contains("-mv") ? (uint?)uint.Parse(args[argList.IndexOf("-mv") + 1]) : null;
            bool recalculateOutputMinMax = args.Contains("-no");;
            bool boost = !args.Contains("-nb");
            string limitCard = args.Contains("-c") ? args[argList.IndexOf("-c") + 1] : (args.Contains("-a") ? "All" : null);
            string outputFeature = args.Contains("-o") ? args[argList.IndexOf("-o") + 1] : "player_final_score";
            uint epochWindow = args.Contains("-e") ? uint.Parse(args[argList.IndexOf("-e") + 1]) : 20;
            uint maxEpochs = args.Contains("-me") ? uint.Parse(args[argList.IndexOf("-me") + 1]) : uint.MaxValue;
            bool sigmoidOutputs = args.Contains("-s");
            double min = args.Contains("-nmin") ? double.Parse(args[argList.IndexOf("-nmin") + 1]) : 0.0;
            double max = args.Contains("-nmax") ? double.Parse(args[argList.IndexOf("-nmax") + 1]) : 0.0;
            if (args.Contains("-p"))
            {
                LearnerFactory.Learner = LearnerFactory.Learners.Perceptron;
            }

            Console.WriteLine("Parameters: <> means argument, = means default value");
            Console.WriteLine(" -f <file=test.db3>    Use database file");
            Console.WriteLine(" -c <card>             Train only on a single card rather than all\n" +
                              "                       (spaces should be replaced with underscores,\n" +
                              "                       apostrophes should be left out.)\n" +
                              "                       (if 'Random', then a random card is picked)");
            Console.WriteLine(" -a                    Train using all cards (no filtering on card_bought)\n");
            Console.WriteLine(" -s                    Use a sigmoid output, rather than continuous\n");
            Console.WriteLine(" -o <feature>          Use the given output feature\n" +
                              "                       (default is player_final_score)");
            Console.WriteLine(" -t <train %=0.8>      Approximate percentage of data to use for training");
            Console.WriteLine(" -mt <instances=all>   Max number of instances to train per epoch\n" +
                              "                       (default is however many are in the training set)");
            Console.WriteLine(" -v <validate %=0.2>   Approximate percentage of training data to use for\n" +
                              "                       validation");
            Console.WriteLine(" -mv <instances=all>   Max number of instances to validate per epoch\n" +
                              "                       (default is however many are in the training set)");
            Console.WriteLine(" -e <window=20>        Number of previous epochs to consider in the\n" +
                              "                       stopping window");
            Console.WriteLine(" -me <epochs=MaxInt>   Number of epochs to cap training with");
            Console.WriteLine(" -no                   Recalculate the normalization min/max of the output\n" +
                              "                       (otherwise, the precomputed values are used)");
            Console.WriteLine(" -nmin <min>           Use the given output normalization min");
            Console.WriteLine(" -nmax <max>           Use the given output normalization max");
            Console.WriteLine(" -nb                   Disable boosting of rare features");
            Console.WriteLine(" -p                    Use a perceptron rather than backprop");

            Stopwatch watch = Stopwatch.StartNew();

            // Get the global properties from the database before starting all the subtasks.
            // Each subtask will initiate its own memory database.
            IList<string> columns;
            IList<string> features;
            IList<string> cards;
            double average = 0.0;
            double stddev = 0.0;
            using (SQLiteConnection conn = new SQLiteConnection(string.Format("Data Source={0};Version=3;", file)))
            {
                conn.Open();

                // Get the list of features from the table column names
                columns = conn.GetTableColumns("instances");

                // Normalization data
                if (recalculateOutputMinMax)
                {
                    string sql = @"SELECT AVG(`player_final_score`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        average = Convert.ToDouble(command.ExecuteScalar());
                    }
                    sql = @"SELECT AVG((`instances`.`player_final_score` - `sub`.`a`)*(`instances`.`player_final_score` - `sub`.`a`)) AS `var` FROM `instances`, (SELECT AVG(`player_final_score`) AS `a` FROM `instances`) AS `sub`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        stddev = Math.Sqrt(Convert.ToDouble(command.ExecuteScalar()));
                    }
                }
                else
                {
                    // Cached values calculated on the complete March dataset.
                    average = 38.25765735;
                    stddev = 18.68538455;
                }
                if (min == 0.0 && max == 0.0)
                {
                    min = average - 2 * stddev; // This should catch about 95% of all games within this normalization region, assuming this does indeed have a mostly normal distribution.
                    max = average + 2 * stddev;
                }

                Console.WriteLine("Average: {0}", average);
                Console.WriteLine("Std Dev: {0}", stddev);
                Console.WriteLine("Min:     {0}", min);
                Console.WriteLine("Max:     {0}", max);

                features = columns.Where(IsFeatureColumn).ToList();

                // Get the list of cards that should be trained
                if (!string.IsNullOrWhiteSpace(limitCard))
                {
                    if (limitCard.Equals("Random", StringComparison.OrdinalIgnoreCase))
                    {
                        Random rand = new Random();
                        cards = GetCards(conn).OrderBy(card => rand.Next()).Take(1).ToList();
                    }
                    else
                    {
                        cards = new List<string>();
                        cards.Add(limitCard);
                    }
                }
                else
                {
                    // Sort the cards so that the basic cards (which have more instances) are run first.
                    // This prevents them from lingering on after everything else has finished.
                    cards = GetCards(conn).OrderBy(card =>
                    {
                        if (card == "Estate" || card == "Duchy" || card == "Province" || card == "Colony" ||
                            card == "Copper" || card == "Silver" || card == "Gold" || card == "Platinum" ||
                            card == "Potion" || card == "None")
                        {
                            return "0" + card;
                        }
                        else
                        {
                            return "1" + card;
                        }
                    }).ToList();
                }
            }

            // Create each of the tasks
            DominionLearnerTask[] learnerTasks = new DominionLearnerTask[cards.Count];
            Task<TaskResult>[] tasks = new Task<TaskResult>[cards.Count];
            for (int i = 0; i < cards.Count; i++)
            {
                learnerTasks[i] = new DominionLearnerTask(cards[i], features, outputFeature, file, trainingPercent, validationPercent, min, max, boost, sigmoidOutputs, maxTrainings, maxValidations, epochWindow, maxEpochs);
                tasks[i] = new Task<TaskResult>(learnerTasks[i].RunTask);
            }

            // Start running some tasks
            int concurrentTasks = Math.Min(System.Environment.ProcessorCount, cards.Count);
            int nextTaskToRun = concurrentTasks;
            Action<Task<TaskResult>> runNextTaskLoop = null;
            Action<Task<TaskResult>> runNextTask = task =>
            {
                if (nextTaskToRun < tasks.Length)
                {
                    tasks[nextTaskToRun].Start();
                    tasks[nextTaskToRun].ContinueWith(t => runNextTaskLoop(t));
                    nextTaskToRun++;
                }
            };
            runNextTaskLoop = runNextTask;
            for (int i = 0; i < concurrentTasks; i++)
            {
                tasks[i].Start();
                tasks[i].ContinueWith(runNextTask);
            }

            // Wait for all of them to run
            Task.WaitAll(tasks);

            Console.WriteLine("All Tasks Complete!");
            watch.Stop();

            TaskResult finalResult = new TaskResult();
            foreach (Task<TaskResult> task in tasks)
            {
                finalResult.Add(task.Result);
            }
            double avgEpochs = (double)finalResult.Epochs / tasks.Length;
            double avgInstancesTrained = (double)finalResult.TotalInstancesTrained / tasks.Length;
            finalResult.TrainingMSE = finalResult.TrainingSSE / finalResult.TrainingInstances;
            finalResult.ValidationMSE = finalResult.ValidationSSE / finalResult.ValidationInstances;
            finalResult.TestingMSE = finalResult.TestingSSE / finalResult.TestingInstances;

            using (StreamWriter log = new StreamWriter(String.Format("{0}\\Final.txt", LearnerFactory.Folder), false))
            {
                log.WriteLine("All Training Complete! (Took {0} hours, {1} minutes, {2} seconds and trained {3} cards)", Math.Floor(watch.Elapsed.TotalHours), watch.Elapsed.Minutes, watch.Elapsed.Seconds, cards.Count);
                log.WriteLine(" Trained a total of {0} instances over {1} epochs", finalResult.TotalInstancesTrained, finalResult.Epochs);
                log.WriteLine(" Trained an average of {0} instances over {1} epochs", Math.Round(avgInstancesTrained), Math.Round(avgEpochs, 2));
                log.WriteLine(" Total SSE (training sets):   {0:.0000000000} ({1:.0000000000})", finalResult.TrainingSSE, UnNormalize(Math.Sqrt(finalResult.TrainingSSE), min, max));
                log.WriteLine(" Total SSE (validation sets): {0:.0000000000} ({1:.0000000000})", finalResult.ValidationSSE, UnNormalize(Math.Sqrt(finalResult.ValidationSSE), min, max));
                log.WriteLine(" Total SSE (testing sets):    {0:.0000000000} ({1:.0000000000})", finalResult.TestingSSE, UnNormalize(Math.Sqrt(finalResult.TestingSSE), min, max));
                log.WriteLine(" Total MSE (training sets):   {0:.0000000000} ({1:.0000000000})", finalResult.TrainingMSE, UnNormalize(Math.Sqrt(finalResult.TrainingMSE), min, max));
                log.WriteLine(" Total MSE (validation sets): {0:.0000000000} ({1:.0000000000})", finalResult.ValidationMSE, UnNormalize(Math.Sqrt(finalResult.ValidationMSE), min, max));
                log.WriteLine(" Total MSE (testing sets):    {0:.0000000000} ({1:.0000000000})", finalResult.TestingMSE, UnNormalize(Math.Sqrt(finalResult.TestingMSE), min, max));
            }

            Console.WriteLine("All Training Complete! (Took {0} hours, {1} minutes, {2} seconds and trained {3} cards)", Math.Floor(watch.Elapsed.TotalHours), watch.Elapsed.Minutes, watch.Elapsed.Seconds, cards.Count);
            Console.WriteLine(" Trained a total of {0} instances over {1} epochs", finalResult.TotalInstancesTrained, finalResult.Epochs);
            Console.WriteLine(" Trained an average of {0} instances over {1} epochs", Math.Round(avgInstancesTrained), Math.Round(avgEpochs, 2));
            Console.WriteLine(" Total SSE (training sets):   {0:.0000000000} ({1:.0000000000})", finalResult.TrainingSSE, UnNormalize(Math.Sqrt(finalResult.TrainingSSE), min, max));
            Console.WriteLine(" Total SSE (validation sets): {0:.0000000000} ({1:.0000000000})", finalResult.ValidationSSE, UnNormalize(Math.Sqrt(finalResult.ValidationSSE), min, max));
            Console.WriteLine(" Total SSE (testing sets):    {0:.0000000000} ({1:.0000000000})", finalResult.TestingSSE, UnNormalize(Math.Sqrt(finalResult.TestingSSE), min, max));
            Console.WriteLine(" Total MSE (training sets):   {0:.0000000000} ({1:.0000000000})", finalResult.TrainingMSE, UnNormalize(Math.Sqrt(finalResult.TrainingMSE), min, max));
            Console.WriteLine(" Total MSE (validation sets): {0:.0000000000} ({1:.0000000000})", finalResult.ValidationMSE, UnNormalize(Math.Sqrt(finalResult.ValidationMSE), min, max));
            Console.WriteLine(" Total MSE (testing sets):    {0:.0000000000} ({1:.0000000000})", finalResult.TestingMSE, UnNormalize(Math.Sqrt(finalResult.TestingMSE), min, max));
        }

        public static double UnNormalize(double value, double min, double max)
        {
            return (value * (max - min)) + min;
        }


        // These are the hard coded, known non-feature column names.
        // If other features should be excluded, they can be added to this list.
        private static string[] nonFeatureColumns = { "id", "card_bought", "card_output_weight", "player_current_score", "player_score_increase", "player_final_score", "average_final_score", "player_won", "player_gained_victory_cards", "player_gained_core_victory_cards", "randomizer", "use", "game_id", "game_year", "game_month", "game_day", "game_hour", "game_minute", "game_second" };
        public static bool IsFeatureColumn(string column)
        {
            return !nonFeatureColumns.Contains(column);
        }

        public static IList<string> GetCards(SQLiteConnection conn)
        {
            string sql = @"SELECT DISTINCT `card_bought` FROM `instances` ORDER BY `card_bought` ASC;";

            List<string> cards = new List<string>();
            using (SQLiteCommand command = new SQLiteCommand(sql, conn))
            {
                SQLiteDataReader reader = command.ExecuteReader();
                while (reader.Read())
                {
                    cards.Add((string)reader["card_bought"]);
                }
            }
            return cards;
        }
    }

    public struct TaskResult
    {
        public uint TotalInstances { get; set; }

        public double TrainingSSE { get; set; }
        public double TrainingMSE { get; set; }
        public uint TrainingInstances { get; set; }
        
        public double ValidationSSE { get; set; }
        public double ValidationMSE { get; set; }
        public uint ValidationInstances { get; set; }
        
        public double TestingSSE { get; set; }
        public double TestingMSE { get; set; }
        public uint TestingInstances { get; set; }

        public uint Epochs { get; set; }
        public uint TotalInstancesTrained { get; set; }

        public void Add(TaskResult other)
        {
            TotalInstances += other.TotalInstances;
            TrainingSSE += other.TrainingSSE;
            TrainingMSE += other.TrainingMSE;
            TrainingInstances += other.TrainingInstances;
            ValidationSSE += other.ValidationSSE;
            ValidationMSE += other.ValidationMSE;
            ValidationInstances += other.ValidationInstances;
            TestingSSE += other.TestingSSE;
            TestingMSE += other.TestingMSE;
            TestingInstances += other.TestingInstances;
            Epochs += other.Epochs;
            TotalInstancesTrained += other.TotalInstancesTrained;
        }
    }

    public static class SQLiteExtensions
    {
        public static List<string> GetTableColumns(this SQLiteConnection conn, string table)
        {
            DataTable tableInfo = conn.GetSchema(SQLiteMetaDataCollectionNames.Columns, new string[] { null, null, table });
            List<string> columnNames = new List<string>();
            foreach (DataRow row in tableInfo.Rows)
            {
                columnNames.Add(row.Field<string>("COLUMN_NAME"));
            }
            return columnNames;
        }

        public static double StdDev(this IEnumerable<double> values)
        {
            double ret = 0;
            if (values.Count() > 0)
            {
                //Compute the Average      
                double avg = values.Average();
                //Perform the Sum of (value-avg)_2_2      
                double sum = values.Sum(d => Math.Pow(d - avg, 2));
                //Put it all together      
                ret = Math.Sqrt((sum) / (values.Count() - 1));
            }
            return ret;
        }
    }
}
