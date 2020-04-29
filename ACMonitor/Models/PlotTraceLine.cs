using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACAMonitor.Models
{
    public class PlotTraceLine
    {
        [JsonProperty(NullValueHandling = NullValueHandling.Ignore)]
        public int width { get; set; }
        [JsonProperty(NullValueHandling = NullValueHandling.Ignore)]
        public string color { get; set; }
    }
}
