using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACMonitor.Models
{
    public class SigmaDataEdge
    {
        [JsonProperty(PropertyName = "id")]
        public string Id { get => $"{Source}:{Target}"; }

        [JsonProperty(PropertyName = "source")]
        public string Source { get; set; }

        [JsonProperty(PropertyName = "target")]
        public string Target { get; set; }

        [JsonProperty(PropertyName = "color")]
        public string Color { get; set; } = "black";
    }
}
