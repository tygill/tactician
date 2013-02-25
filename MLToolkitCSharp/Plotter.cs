using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    public class Plotter
    {
        private StreamWriter m_outFile;
        private List<Plot> m_plots;

        public Plotter(string filename)
        {
            m_outFile = new StreamWriter(filename);
            m_plots = new List<Plot>();
        }

        public void addPlot(Plot p)
        {
            m_plots.Add(p);
        }

        public void printPlots()
        {
            using (m_outFile)
            {
                for (int i = 0; i < m_plots.Count; ++i)
                {
                    m_outFile.WriteLine("set term wxt " + i);
                    m_plots[i].print(m_outFile);
                }
            }
        }
    }
}
