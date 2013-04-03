using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
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
            bool rerandomize = args.Contains("-r") || args.Contains("-t") || args.Contains("-v");
            rerandomize = false;
            double trainingPercent = args.Contains("-t") ? double.Parse(args[argList.IndexOf("-t") + 1]) : 0.7;
            double validationPercent = args.Contains("-v") ? double.Parse(args[argList.IndexOf("-v") + 1]) : 0.3;
            bool recalculateOutputMinMax = args.Contains("-o");
            bool recalculateInputMinMax = args.Contains("-i");
            bool boost = !args.Contains("-nb");

            Console.WriteLine("Parameters: <> means argument, = means default value");
            Console.WriteLine(" -f <file=test.db3>    Use database file");
            Console.WriteLine(" -r                    Rerandomize (reset the randomizer and use fields)");
            Console.WriteLine(" -t <train %=0.7>      Approximate percentage of data to use for training\n" +
                              "                       (implies -r - not anymore. Game second is now used)");
            Console.WriteLine(" -v <validate %=0.3>   Approximate percentage of training data to use for\n" +
                              "                       validation (implies -r - not anymore. Second used now)");
            Console.WriteLine(" -o                    Recalculate the normalization min/max of the output\n" +
                              "                       (otherwise, the precomputed values are used)");
            Console.WriteLine(" -i                    Recalculate the normalization min/max for each input\n" +
                              "                       feature (otherwise, precomputed values are used)");
            Console.WriteLine(" -nb                   Disable boosting of rare features");

            // Get the global properties from the database before starting all the subtasks.
            // Each subtask will initiate its own memory database.
            IList<string> columns;
            IList<string> features;
            IDictionary<string, double> featureNormalizationMins = null;
            IDictionary<string, double> featureNormalizationMaxs = null;
            IList<string> cards;
            double average = 0.0;
            double stddev = 0.0;
            double min = 0.0;
            double max = 0.0;
            using (SQLiteConnection conn = new SQLiteConnection(string.Format("Data Source={0};Version=3;", file)))
            {
                conn.Open();

                // Get the list of features from the table column names
                columns = conn.GetTableColumns("instances");

                // Hack in the ALTER TABLE to add the randomizer and use columns (used to divide into validation sets and such)
                /*
                if (!columns.Contains("randomizer"))
                {
                    Console.WriteLine("Adding randomizer column");
                    string sql = @"ALTER TABLE `instances` ADD COLUMN `randomizer` INT;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    rerandomize = true;
                    columns.Add("randomizer");
                }

                if (!columns.Contains("use"))
                {
                    Console.WriteLine("Adding use column");
                    string sql = @"ALTER TABLE `instances` ADD COLUMN `use` TEXT;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    rerandomize = true;
                    columns.Add("use");
                }
                //*/

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
                min = average - 2 * stddev; // This should catch about 95% of all games within this normalization region, assuming this does indeed have a mostly normal distribution.
                max = average + 2 * stddev;

                Console.WriteLine("Average: {0}", average);
                Console.WriteLine("Std Dev: {0}", stddev);
                Console.WriteLine("Min:     {0}", min);
                Console.WriteLine("Max:     {0}", max);

                // Old code for extracting averages and standard deviations and such...
                //double min = 0.0;
                //double max = 1.0;
                /*
                {
                    //string sql = "SELECT MAX(`card_output_weight`) FROM `instances`;";
                    string sql = "SELECT MAX(`player_final_score`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        max = Convert.ToDouble(command.ExecuteScalar());
                    }
                    //sql = "SELECT MIN(`card_output_weight`) FROM `instances`;";
                    sql = "SELECT MIN(`player_final_score`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        min = Convert.ToDouble(command.ExecuteScalar());
                    }
                }
                //*/

                /*
                {
                    string sql = "SELECT AVG(`card_output_weight`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        average = Convert.ToDouble(command.ExecuteScalar());
                    }
                    sql = "SELECT AVG((`instances`.`card_output_weight` - `sub`.`a`)*(`instances`.`card_output_weight` - `sub`.`a`)) AS `var` FROM `instances`, (SELECT AVG(`card_output_weight`) AS `a` FROM `instances`) AS `sub`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        stddev = Math.Sqrt(Convert.ToDouble(command.ExecuteScalar()));
                    }
                }
                //*/

                /*
                if (rerandomize)
                {
                    Console.WriteLine("Rerandomizing training, validation, and testing sets (this will take a while)");
                    string sql;
                    using (SQLiteTransaction transaction = conn.BeginTransaction())
                    {
                        sql = "PRAGMA journal_mode = OFF;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        Console.Write(" .");
                        // Reset the randomizer column (used to divide training, validation, and test sets)
                        sql = "UPDATE `instances` SET `randomizer` = ABS(RANDOM() % 100);";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        Console.Write(".");
                        sql = "DROP INDEX IF EXISTS `use_index`;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        Console.Write(".");
                        // [ training | test ]
                        // [ [ validation | training ] | test ]
                        sql = "UPDATE `instances` SET `use` = (CASE WHEN `randomizer` < @validationCutoff THEN 'validation' WHEN `randomizer` < @trainingCutoff THEN 'training' ELSE 'testing' END);";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.Parameters.AddWithValue("@trainingCutoff", Math.Round(trainingPercent * 100));
                            command.Parameters.AddWithValue("@validationCutoff", Math.Round(trainingPercent * validationPercent * 100));
                            command.ExecuteNonQuery();
                        }
                        Console.Write(".");
                        sql = "CREATE INDEX IF NOT EXISTS `use_index` ON `instances` (`use`);";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        Console.Write(".");
                        sql = "PRAGMA journal_mode = ON;";
                        using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                        {
                            command.ExecuteNonQuery();
                        }
                        transaction.Commit();
                    }
                    Console.Write(".");
                    sql = "VACUUM;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    Console.WriteLine("done");
                }
                //*/

                features = columns.Where(IsFeatureColumn).ToList();

                /*
                // These are actually now being normalized/binned by the extractor.
                // Calculate the normalization min/max for each column
                featureNormalizationMins = new Dictionary<string, double>();
                featureNormalizationMaxs = new Dictionary<string, double>();
                string[] normalized = { "turn_number", "money", "buys", "actions", "player_deck_size", "player_deck_action_cards", "player_deck_victory_cards", "player_deck_treasure_cards" };
                if (recalculateInputMinMax)
                {
                    string minSql = @"SELECT MIN({0}) FROM `instances`;";
                    string maxSql = @"SELECT MAX({0}) FROM `instances`;";
                    using (SQLiteCommand minCommand = new SQLiteCommand(minSql, conn))
                    using (SQLiteCommand maxCommand = new SQLiteCommand(maxSql, conn))
                    {
                        foreach (string feature in features)
                        {
                            double tmpMin = 0.0;
                            double tmpMax = 1.0;
                            if (normalized.Contains(feature))
                            {
                                minCommand.CommandText = string.Format(minSql, feature);
                                maxCommand.CommandText = string.Format(maxSql, feature);
                                tmpMin = Convert.ToDouble(minCommand.ExecuteScalar());
                                tmpMax = Convert.ToDouble(maxCommand.ExecuteScalar());
                            }
                            featureNormalizationMins.Add(feature, tmpMin);
                            featureNormalizationMaxs.Add(feature, tmpMax);
                            Console.WriteLine("Feature Min:\t{0}\t{1}", tmpMin, feature);
                            Console.WriteLine("Feature Max:\t{0}\t{1}", tmpMax, feature);
                        }
                    }
                }
                else
                {
                    // Use the cached normalization min/max
                    foreach (string feature in features)
                    {
                        double tmpMin = 0.0;
                        double tmpMax = 1.0;
                        /*
                        if (normalized.Contains(feature))
                        {
                            if (feature == "turn_number")
                            {
                                tmpMin = 1.0;
                                tmpMax = 61.0;
                            }
                            else if (feature == "money")
                            {
                                tmpMin = 0.0;
                                tmpMax = 20.0; // Max was really 113...
                            }
                            else if (feature == "buys")
                            {
                                tmpMin = 1.0;
                                tmpMax = 5.0; // Max was really 45...
                            }
                            else if (feature == "actions")
                            {
                                tmpMin = 1.0;
                                tmpMax = 20.0; // Max was really 66...
                            }
                            else if (feature == "player_deck_size")
                            {
                                tmpMin = 0.0;
                                tmpMax = 100.0; // Max was really 133...
                            }
                            else if (feature == "player_deck_action_cards")
                            {
                                tmpMin = 0.0;
                                tmpMax = 40.0; // Max was really 55...
                            }
                            else if (feature == "player_deck_victory_cards")
                            {
                                tmpMin = 0.0;
                                tmpMax = 20.0; // Max was really 32...
                            }
                            else if (feature == "player_deck_treasure_cards")
                            {
                                tmpMin = 0.0;
                                tmpMax = 60.0; // Max was really 86...
                            }
                        }
                        //* /
                        featureNormalizationMins.Add(feature, tmpMin);
                        featureNormalizationMaxs.Add(feature, tmpMax);
                    }
                }
                //*/

                // Get the list of cards that should be trained
                cards = GetCards(conn);
                Random rand = new Random();
                //cards = cards.OrderBy(card => rand.Next()).Take(1).ToList(); // Limit it to a single card for testing
                //cards.Clear();
                //cards.Add("None");
            }

            // Create each of the tasks
            DominionLearnerTask[] learnerTasks = new DominionLearnerTask[cards.Count];
            Task<TaskResult>[] tasks = new Task<TaskResult>[cards.Count];
            for (int i = 0; i < cards.Count; i++)
            {
                learnerTasks[i] = new DominionLearnerTask(cards[i], features, file, trainingPercent, validationPercent, min, max, boost, featureNormalizationMins, featureNormalizationMaxs);
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
            TaskResult finalResult;
            foreach (Task<TaskResult> task in tasks)
            {
                finalResult.Add(task.Result);
            }
        }

        // These are the hard coded, known non-feature column names.
        // If other features should be excluded, they can be added to this list.
        private static string[] nonFeatureColumns = { "id", "card_bought", "card_output_weight", "player_final_score", "average_final_score", "randomizer", "use", "game_id", "game_year", "game_month", "game_day", "game_hour", "game_minute", "game_second" };
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
        public double TrainingSSE { get; set; }
        public double TrainingMSE { get; set; }
        public double TrainingInstances { get; set; }
        public double ValidationSSE { get; set; }
        public double ValidationMSE { get; set; }
        public double ValidationInstances { get; set; }
        public double TestingSSE { get; set; }
        public double TestingMSE { get; set; }
        public double TestingInstances { get; set; }

        public void Add(TaskResult other)
        {
            TrainingSSE += other.TrainingSSE;
            TrainingMSE += other.TrainingMSE;
            TrainingInstances += other.TrainingInstances;
            ValidationSSE += other.ValidationSSE;
            ValidationMSE += other.ValidationMSE;
            ValidationInstances += other.ValidationInstances;
            TestingSSE += other.TestingSSE;
            TestingMSE += other.TestingMSE;
            TestingInstances += other.TestingInstances;
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
