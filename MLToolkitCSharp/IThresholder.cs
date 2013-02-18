using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MLToolkitCSharp
{
    interface IThresholder
    {
        double thresholdValue(double val);
    }
}
