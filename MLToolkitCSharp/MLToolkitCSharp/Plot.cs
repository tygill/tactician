using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    public class Plot
    {
        public string Title { get; set; }
        public string XLabel { get; set; }
        public string YLabel { get; set; }
        public int? XMin { get; set; }
        public int? XMax { get; set; }
        public int? YMin { get; set; }
        public int? YMax { get; set; }

        private List<Tuple<double, double>> m_dataPoints;

        public Plot(String title)
        {
            Title = title;
            XLabel = null;
            YLabel = null;
            XMin = null;
            XMax = null;
            YMin = null;
            YMax = null;
            m_dataPoints = new List<Tuple<double, double>>();
        }

        public void addDataPoint(double x, double y)
        {
            m_dataPoints.Add(new Tuple<double, double>(x, y));
        }

        public void print(StreamWriter outFile)
        {
            printHeader(outFile);
            printData(outFile);
        }

        private void printHeader(StreamWriter outFile)
        {
            outFile.WriteLine("unset key");
            outFile.WriteLine("set title \"" + Title + "\"");

            if (XLabel != null)
                outFile.WriteLine("set xlabel \"" + XLabel + "\"");
            if (XMin != null && XMax != null)
                outFile.WriteLine("set xrange[" + XMin + ": " + XMax + "]");

            if (YLabel != null)
                outFile.WriteLine("set ylabel \"" + YLabel + "\"");
            if (YMin != null && YMax != null)
                outFile.WriteLine("set yrange[" + YMin + ": " + YMax + "]");
        }

        private void printData(StreamWriter outFile)
        {
            outFile.WriteLine("plot '-' with line lt 3");
            foreach (Tuple<double, double> dataPt in m_dataPoints)
                outFile.WriteLine(dataPt.Item1 + ", " + dataPt.Item2);
            outFile.WriteLine("e");
        }
    }
}
