using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace ACMonitor.Services
{
    public static class StatisticCalculator
    {
        public static double? CalculatePercentError(double? avgStates, double? avgReferenceSignals)
        {
            if (!avgStates.HasValue || !avgReferenceSignals.HasValue)
            {
                return null;
            }

            var error = Math.Abs((avgStates.Value - avgReferenceSignals.Value) / avgReferenceSignals.Value) * 100;

            return error;
        }

        public static double CalculatePercentDifferencePeak(params double[] states)
        {
            if (states.Length == 0)
            {
                throw new ArgumentException("Sates required.");
            }
            var max = states.Max();
            var min = states.Min();

            if (max+min == 0 || max-min == 0)
                return 0;

            var diff = Math.Abs((max - min) / (max + min));
            
            diff = diff <= 1 ? diff : Math.Pow(diff,-1); // Invert if max > 0 and min <0
            
            diff *=200;

            return diff;
        }

        public static double CalculatePercentDifferenceMedianMean(params double[] states)
        {
            if (states.Length == 0)
            {
                throw new ArgumentException("Sates required.");
            }
            var max = states.Max();
            var min = states.Min();

            var sortedStates = states.OrderBy(n => n);

            double median;

            var count = sortedStates.Count();
            var indexMid = count / 2;
            if ((sortedStates.Count() % 2) == 0)
            {
                median = ((sortedStates.ElementAt(indexMid) +
                    sortedStates.ElementAt((indexMid - 1))) / 2);
            }
            else
            {
                median = sortedStates.ElementAt(indexMid);
            }

            var mean = states.Average();

            var diff = Math.Abs((median - mean) / (median + mean));

            return diff;
        }

        // params: Index 0: n-2, Index 1 : n-1: index 3: n, index 4: n+1
        public static double CalculateConvergenceRate(params double[] x)
        {
            if (x.Length != 4)
                return -1;
            if (x[0] == x[1] || x[1] == x[2])
                return  -1; // division by zero
            
            return Math.Log(Math.Abs((x[3] - x[2]) / (x[2] - x[1]))) / Math.Log(Math.Abs((x[2] - x[1]) / (x[1] - x[0])));
        }
    }
}
