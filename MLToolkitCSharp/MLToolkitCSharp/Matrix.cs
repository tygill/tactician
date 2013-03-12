// ----------------------------------------------------------------
// The contents of this file are distributed under the CC0 license.
// See http://creativecommons.org/publicdomain/zero/1.0/
// ----------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MLToolkitCSharp
{
    public class Matrix
    {
        // Data
        List<double[]> m_data;

        // Meta-data
        List<string> m_attr_name;
        List<Dictionary<string, int>> m_str_to_enum;
        List<Dictionary<int, string>> m_enum_to_str;

        static double MISSING = double.MaxValue; // representation of missing values in the dataset

        // Creates a 0x0 matrix. You should call loadARFF or setSize next.
        public Matrix() { }

        // Copies the specified portion of that matrix into this matrix
        public Matrix(Matrix that, int rowStart, int colStart, int rowCount, int colCount)
        {
            m_data = new List<double[]>();
            for (int j = 0; j < rowCount; j++)
            {
                double[] rowSrc = that.row(rowStart + j);
                double[] rowDest = new double[colCount];
                for (int i = 0; i < colCount; i++)
                    rowDest[i] = rowSrc[colStart + i];
                m_data.Add(rowDest);
            }
            m_attr_name = new List<string>();
            m_str_to_enum = new List<Dictionary<string, int>>();
            m_enum_to_str = new List<Dictionary<int, string>>();
            for (int i = 0; i < colCount; i++)
            {
                m_attr_name.Add(that.attrName(colStart + i));
                m_str_to_enum.Add(that.m_str_to_enum[colStart + i]);
                m_enum_to_str.Add(that.m_enum_to_str[colStart + i]);
            }
        }

        // Adds a copy of the specified portion of that matrix to this matrix
        public void add(Matrix that, int rowStart, int colStart, int rowCount)
        {
            if (colStart + cols() > that.cols())
                throw new Exception("out of range");
            for (int i = 0; i < cols(); i++)
            {
                if (that.valueCount(colStart + i) != valueCount(i))
                    throw new Exception("incompatible relations");
            }
            for (int j = 0; j < rowCount; j++)
            {
                double[] rowSrc = that.row(rowStart + j);
                double[] rowDest = new double[cols()];
                for (int i = 0; i < cols(); i++)
                    rowDest[i] = rowSrc[colStart + i];
                m_data.Add(rowDest);
            }
        }

        // Resizes this matrix (and sets all attributes to be continuous)
        public void setSize(int rows, int cols)
        {
            m_data = new List<double[]>();
            for (int j = 0; j < rows; j++)
            {
                double[] row = new double[cols];
                m_data.Add(row);
            }
            m_attr_name = new List<string>();
            m_str_to_enum = new List<Dictionary<string, int>>();
            m_enum_to_str = new List<Dictionary<int, string>>();
            for (int i = 0; i < cols; i++)
            {
                m_attr_name.Add("");
                m_str_to_enum.Add(new Dictionary<string, int>());
                m_enum_to_str.Add(new Dictionary<int, string>());
            }
        }

        // Loads from an ARFF file
        public void loadArff(String filename)
        {
            m_data = new List<double[]>();
            m_attr_name = new List<string>();
            m_str_to_enum = new List<Dictionary<string, int>>();
            m_enum_to_str = new List<Dictionary<int, string>>();
            bool READDATA = false;
            using (StreamReader s = new StreamReader(filename))
            {
                while (!s.EndOfStream)
                {
                    string line = s.ReadLine().Trim();
                    if (line.Length > 0 && !line.StartsWith("%"))
                    {
                        if (!READDATA)
                        {
                            string[] tokens = line.Split((string[])null, StringSplitOptions.RemoveEmptyEntries);
                            IEnumerator<string> t = tokens.AsEnumerable<string>().GetEnumerator();

                            t.MoveNext();
                            string firstToken = t.Current;

                            if (firstToken.Equals("@RELATION", StringComparison.OrdinalIgnoreCase))
                            {
                                t.MoveNext();
                                string datasetName = t.Current;
                            }

                            if (firstToken.Equals("@ATTRIBUTE", StringComparison.OrdinalIgnoreCase))
                            {
                                Dictionary<string, int> ste = new Dictionary<string, int>();
                                m_str_to_enum.Add(ste);
                                Dictionary<int, string> ets = new Dictionary<int, string>();
                                m_enum_to_str.Add(ets);

                                // Note: This port does not take into account quote escaped attributes as the Java
                                // version does. It appears the C++ version of the toolkit doesn't do this either,
                                // so hopefully this is justified.
                                t.MoveNext();
                                string attributeName = t.Current;
                                if (line.Contains("'"))
                                {
                                    string[] tokens2 = line.Split('\'');
                                    t = tokens2.AsEnumerable<string>().GetEnumerator();
                                    t.MoveNext();
                                    t.MoveNext();
                                    attributeName = "'" + t.Current + "'";
                                }
                                m_attr_name.Add(attributeName);

                                int vals = 0;
                                t.MoveNext();
                                string type = t.Current.Trim();
                                if (type.Equals("REAL", StringComparison.OrdinalIgnoreCase) || type.Equals("CONTINUOUS", StringComparison.OrdinalIgnoreCase) || type.Equals("INTEGER", StringComparison.OrdinalIgnoreCase))
                                {
                                }
                                else
                                {
                                    try
                                    {
                                        string[] values = line.Substring(line.IndexOf("{") + 1).Trim('}').Split(',');
                                        IEnumerator<string> v = values.AsEnumerable<string>().GetEnumerator();
                                        while (v.MoveNext())
                                        {
                                            String value = v.Current.Trim();
                                            if (value.Length > 0)
                                            {
                                                ste.Add(value, vals);
                                                ets.Add(vals, value);
                                                vals++;
                                            }
                                        }
                                    }
                                    catch (Exception e)
                                    {
                                        throw new Exception("Error parsing line: " + line + "\n" + e.Message);
                                    }
                                }
                            }

                            if (firstToken.Equals("@DATA", StringComparison.OrdinalIgnoreCase))
                            {
                                READDATA = true;
                            }
                        }
                        else
                        {
                            double[] newrow = new double[cols()];
                            int curPos = 0;

                            try
                            {
                                string[] tokens = line.Split(',');
                                IEnumerator<string> t = tokens.AsEnumerable<string>().GetEnumerator();
                                while (t.MoveNext())
                                {
                                    String textValue = t.Current.Trim();
                                    //Console.WriteLine(textValue);

                                    if (textValue.Length > 0)
                                    {
                                        double doubleValue;
                                        int vals = m_enum_to_str[curPos].Count;

                                        // Missing instances appear in the dataset as a double defined as MISSING
                                        if (textValue.Equals("?"))
                                        {
                                            doubleValue = MISSING;
                                        }
                                        // Continuous values appear in the instance vector as they are
                                        else if (vals == 0)
                                        {
                                            doubleValue = Double.Parse(textValue);
                                        }
                                        // Discrete values appear as an index to the "name" 
                                        // of that value in the "attributeValue" structure
                                        else
                                        {
                                            doubleValue = m_str_to_enum[curPos][textValue];
                                            if (doubleValue == -1)
                                            {
                                                throw new Exception("Error parsing the value '" + textValue + "' on line: " + line);
                                            }
                                        }

                                        newrow[curPos] = doubleValue;
                                        curPos++;
                                    }
                                }
                            }
                            catch (Exception e)
                            {
                                throw new Exception("Error parsing line: " + line + "\n" + e.Message);
                            }
                            m_data.Add(newrow);
                        }
                    }
                }
            }
        }

        // Returns the number of rows in the matrix
        public int rows() { return m_data.Count; }

        // Returns the number of columns (or attributes) in the matrix
        public int cols() { return m_attr_name.Count; }

        // Returns the specified row
        public double[] row(int r) { return m_data[r]; }

        // Returns the element at the specified row and column
        public double get(int r, int c) { return m_data[r][c]; }

        // Sets the value at the specified row and column
        public void set(int r, int c, double v) { row(r)[c] = v; }

        // Returns the name of the specified attribute
        public String attrName(int col) { return m_attr_name[col]; }

        // Set the name of the specified attribute
        public void setAttrName(int col, String name) { m_attr_name[col] = name; }

        // Returns the name of the specified value
        public String attrValue(int attr, int val) { return m_enum_to_str[attr][val]; }

        // Returns the number of values associated with the specified attribute (or column)
        // 0=continuous, 2=binary, 3=trinary, etc.
        public int valueCount(int col) { return m_enum_to_str[col].Count; }

        // Shuffles the row order
        public void shuffle(Random rand)
        {
            for (int n = rows(); n > 0; n--)
            {
                int i = rand.Next(n);
                double[] tmp = row(n - 1);
                m_data[n - 1] = row(i);
                m_data[i] = tmp;
            }
        }

        // Returns the mean of the specified column
        public double columnMean(int col)
        {
            double sum = 0;
            int count = 0;
            for (int i = 0; i < rows(); i++)
            {
                double v = get(i, col);
                if (v != MISSING)
                {
                    sum += v;
                    count++;
                }
            }
            return sum / count;
        }

        // Returns the min value in the specified column
        public double columnMin(int col)
        {
            double m = MISSING;
            for (int i = 0; i < rows(); i++)
            {
                double v = get(i, col);
                if (v != MISSING)
                {
                    if (m == MISSING || v < m)
                    {
                        m = v;
                    }
                }
            }
            return m;
        }

        // Returns the max value in the specified column
        public double columnMax(int col)
        {
            double m = MISSING;
            for (int i = 0; i < rows(); i++)
            {
                double v = get(i, col);
                if (v != MISSING)
                {
                    if (m == MISSING || v > m)
                    {
                        m = v;
                    }
                }
            }
            return m;
        }

        // Returns the most common value in the specified column
        public double mostCommonValue(int col)
        {
            Dictionary<double, int> tm = new Dictionary<double, int>();
            for (int i = 0; i < rows(); i++)
            {
                double v = get(i, col);
                if (v != MISSING)
                {
                    if (!tm.ContainsKey(v))
                    {
                        tm.Add(v, 1);
                    }
                    else
                    {
                        tm[v] = tm[v] + 1;
                    }
                }
            }
            int maxCount = 0;
            double val = MISSING;
            Dictionary<double, int>.Enumerator it = tm.GetEnumerator();
            while (it.MoveNext())
            {
                KeyValuePair<double, int> e = it.Current;
                if (e.Value > maxCount)
                {
                    maxCount = e.Value;
                    val = e.Key;
                }
            }
            return val;
        }

        public void normalize()
        {
            for (int i = 0; i < cols(); i++)
            {
                if (valueCount(i) == 0)
                {
                    double min = columnMin(i);
                    double max = columnMax(i);
                    for (int j = 0; j < rows(); j++)
                    {
                        double v = get(j, i);
                        if (v != MISSING)
                        {
                            set(j, i, (v - min) / (max - min));
                        }
                    }
                }
            }
        }

        public void print()
        {
            Console.WriteLine("@RELATION Untitled");
            for (int i = 0; i < m_attr_name.Count; i++)
            {
                Console.Write("@ATTRIBUTE " + m_attr_name[i]);
                int vals = valueCount(i);
                if (vals == 0)
                {
                    Console.WriteLine(" CONTINUOUS");
                }
                else
                {
                    Console.Write(" {");
                    for (int j = 0; j < vals; j++)
                    {
                        if (j > 0)
                        {
                            Console.Write(", ");
                        }
                        Console.Write(m_enum_to_str[i][j]);
                    }
                    Console.WriteLine("}");
                }
            }
            Console.WriteLine("@DATA");
            for (int i = 0; i < rows(); i++)
            {
                double[] r = row(i);
                for (int j = 0; j < r.Length; j++)
                {
                    if (j > 0)
                    {
                        Console.Write(", ");
                    }
                    if (valueCount(j) == 0)
                    {
                        Console.Write(r[j]);
                    }
                    else
                    {
                        Console.Write(m_enum_to_str[j][(int)r[j]]);
                    }
                }
                Console.WriteLine("");
            }
        }
    }
}
