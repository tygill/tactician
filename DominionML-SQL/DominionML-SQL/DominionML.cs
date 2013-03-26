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
            double trainingPercent = args.Contains("-t") ? double.Parse(args[argList.IndexOf("-t") + 1]) : 0.7;
            double validationPercent = args.Contains("-v") ? double.Parse(args[argList.IndexOf("-v") + 1]) : 0.3;
            Console.WriteLine("Parameters: <> means argument, = means default value");
            Console.WriteLine(" -f <file=test.db3>    Use database file");
            Console.WriteLine(" -r                    Rerandomize (reset the randomizer and use fields)");
            Console.WriteLine(" -t <train %=0.7>      Approximate percentage of data to use for training (implies -r)");
            Console.WriteLine(" -v <validate %=0.3>   Approximate percentage of training data to use for validation (implies -r)");

            using (SQLiteConnection conn = new SQLiteConnection(string.Format("Data Source={0};Version=3;", file)))
            {
                conn.Open();

                // Get the list of features from the table column names
                IList<string> columns = conn.GetTableColumns("instances");

                // Hack in the ALTER TABLE to add the randomizer and use columns (used to divide into validation sets and such)
                ///*
                if (!columns.Contains("randomizer"))
                {
                    Console.WriteLine("Adding randomizer column");
                    string sql = "ALTER TABLE `instances` ADD COLUMN `randomizer` INT;";
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
                    string sql = "ALTER TABLE `instances` ADD COLUMN `use` TEXT;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    rerandomize = true;
                    columns.Add("use");
                }
                //*/

                // Normalization data
                //*
                double average = 0.0;
                double stddev = 0.0;
                double median = 0.0;
                {
                    string sql = "SELECT `player_final_score` FROM `instances` ORDER BY `player_final_score`";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        using (SQLiteDataReader reader = command.ExecuteReader())
                        {
                            List<double> scores = new List<double>();
                            while (reader.Read())
                            {
                                scores.Add(reader.GetDouble(0));
                            }
                            average = scores.Average();
                            stddev = scores.StdDev();
                            median = scores[scores.Count / 2];
                        }
                    }
                }
                //*/
                double min = average - 2 * stddev; // This should catch about 95% of all games within this normalization region, assuming this does indeed have a mostly normal distribution.
                double max = average + 2 * stddev;

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

                ///*
                if (rerandomize)
                {
                    Console.WriteLine("Rerandomizing training, validation, and testing sets (this will take a while)");
                    string sql = "PRAGMA journal_mode = OFF;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    // Reset the randomizer column (used to divide training, validation, and test sets)
                    sql = "UPDATE `instances` SET `randomizer` = ABS(RANDOM() % 100);";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    Console.Write(" .");
                    sql = "DROP INDEX IF EXISTS `use_index`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    // [ training | test ]
                    // [ [ validation | training ] | test ]
                    sql = "UPDATE `instances` SET `use` = (CASE WHEN `randomizer` < (@trainingPercent * @validationPercent) * 100 THEN 'validation' WHEN `randomizer` < @trainingPercent * 100 THEN 'training' ELSE 'testing' END);";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.Parameters.AddWithValue("@trainingPercent", trainingPercent);
                        command.Parameters.AddWithValue("@validationPercent", validationPercent);
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
                    Console.WriteLine("done");
                }
                //*/

                IEnumerable<string> features = columns.Where(IsFeatureColumn);
                // Build the string to int mapping for column indexes
                Dictionary<string, int> featureIndexes = new Dictionary<string, int>();
                int index = 0;
                foreach (string feature in features)
                {
                    featureIndexes.Add(feature, index++);
                }

                // Get the list of cards that should be trained
                IList<string> cards = GetCards(conn);
                //cards = cards.Take(1).ToList(); // Limit it to a single card for testing

                // Create each of the tasks
                DominionLearnerTask[] learnerTasks = new DominionLearnerTask[cards.Count];
                Task[] tasks = new Task[cards.Count];
                for (int i = 0; i < cards.Count; i++)
                {
                    learnerTasks[i] = new DominionLearnerTask(cards[i], features, conn, min, max);
                    tasks[i] = Task.Factory.StartNew(learnerTasks[i].RunTask);
                }
                // Wait for all of them to run
                Task.WaitAll(tasks);
                // Dispose everything
                foreach (DominionLearnerTask learnerTask in learnerTasks)
                {
                    learnerTask.Dispose();
                }

                Console.ReadLine();
            }
        }

        // These are the hard coded, known non-feature column names.
        // If other features should be excluded, they can be added to this list.
        private static string[] nonFeatureColumns = { "id", "card_bought", "card_output_weight", "player_final_score", "average_final_score", "randomizer", "use" };
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
