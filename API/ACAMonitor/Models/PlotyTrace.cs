using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACAMonitor.Models
{
    public class PlotyTrace
    {
        public List<double> x { get; set; } = new List<double>();
        public List<double> y { get; set; } = new List<double>();
        public string type { get; set; } = "scatter";
        public string name { get; set; }
        [JsonProperty(NullValueHandling = NullValueHandling.Ignore)]
        public PlotTraceLine line { get; set; }
        [JsonProperty(NullValueHandling = NullValueHandling.Ignore)]
        public PlotTraceLine marker { get; set; }
    }
}
