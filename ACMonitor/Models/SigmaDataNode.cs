using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACMonitor.Models
{
    public class SigmaDataNode
    {
        [JsonProperty(PropertyName = "id")]
        public string Id { get; set; }

        [JsonProperty(PropertyName = "label")]
        public string Label { get; set; }

        [JsonProperty(PropertyName = "x")]
        public int X { get; set; } = new Random().Next();

        [JsonProperty(PropertyName = "y")]
        public int Y { get; set; } = new Random().Next();

        [JsonProperty(PropertyName = "size")]
        public int Size { get; set; }

        [JsonProperty(PropertyName = "color")]
        public string Color { get; set; } = "green";
    }
}
