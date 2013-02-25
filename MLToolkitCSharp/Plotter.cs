using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    public class Plotter
    {
        private string m_filename;
        private List<Plot> m_plots;

        public Plotter(string filename)
        {
            m_filename = filename;
            m_plots = new List<Plot>();
        }

        public void addPlot(Plot p)
        {
            m_plots.Add(p);
        }

        public void printPlots()
        {
            using (StreamWriter outFile = new StreamWriter(m_filename))
            {
                for (int i = 0; i < m_plots.Count; ++i)
                {
                    outFile.WriteLine("set term wxt " + i);
                    m_plots[i].print(outFile);
                }
            }
        }
    }
}
