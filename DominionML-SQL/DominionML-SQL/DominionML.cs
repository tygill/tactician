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
            string file = args.Contains("-f") ? args[argList.IndexOf("-F") + 1] : "test.db3";
            bool rerandomize = args.Contains("-r");

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
                    sql = "CREATE INDEX IF NOT EXISTS `use_index` ON `instances` (`use`);";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.ExecuteNonQuery();
                    }
                    rerandomize = true;
                    columns.Add("use");
                }
                //*/

                // Normalization data
                double min = -1.0; // hand picked for now...
                double max = 1.0;
                /*
                {
                    string sql = "SELECT MAX(`card_output_weight`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        max = Convert.ToDouble(command.ExecuteScalar());
                    }
                    sql = "SELECT MIN(`card_output_weight`) FROM `instances`;";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        min = Convert.ToDouble(command.ExecuteScalar());
                    }
                }
                //*/

                /*
                {
                    string sql = "SELECT `card_output_weight` FROM `instances` ORDER BY `card_output_weight`";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        using (SQLiteDataReader reader = command.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                Console.WriteLine(reader.GetDouble(0));
                            }
                        }
                    }
                    System.Environment.Exit(0);
                }
                //*/

                /*
                double average = 0.0;
                double stddev = 0.0;
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
                Console.WriteLine("Average: {0}", average);
                Console.WriteLine("Std Dev: {0}", stddev);
                min = average - 3 * stddev;
                max = average + 3 * stddev;
                //*/
                Console.WriteLine("Min: {0}", min);
                Console.WriteLine("Max: {0}", max);

                ///*
                if (rerandomize)
                {
                    Console.Write("Rerandomizing training, validation, and testing sets...");
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
                    // [ training | test ]
                    // [ [ validation | training ] | test ]
                    sql = "UPDATE `instances` SET `use` = (CASE WHEN `randomizer` < (@trainingPercent * @validationPercent) * 100 THEN 'validation' WHEN `randomizer` < @trainingPercent * 100 THEN 'training' ELSE 'test' END);";
                    using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                    {
                        command.Parameters.AddWithValue("@trainingPercent", 0.7);
                        command.Parameters.AddWithValue("@validationPercent", 0.3);
                        command.ExecuteNonQuery();
                    }
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

                /*
                string sql = string.Format(@"SELECT `{0}` FROM `instances` WHERE `card_bought` = @card_bought ORDER BY RANDOM()", string.Join("`, `", features));
                //Console.WriteLine("SQL: {0}", sql);

                using (SQLiteCommand command = new SQLiteCommand(sql, conn))
                {
                    command.Parameters.AddWithValue("@card_bought", "Alchemist");
                    //Console.WriteLine(" SQL: {0}", command.);
                    SQLiteDataReader reader = command.ExecuteReader();
                    while (reader.Read())
                    {
                        Console.WriteLine(" Row: ALchemist: {0}", reader["alchemist_in_supply"]);
                    }
                }
                 */
            }
        }

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
