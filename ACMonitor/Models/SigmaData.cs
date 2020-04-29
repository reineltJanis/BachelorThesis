using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACAMonitor.Models
{
    public class SigmaData
    {
        [JsonProperty(PropertyName = "nodes")]
        public IEnumerable<SigmaDataNode> Nodes { get; set; } = new List<SigmaDataNode>();
        [JsonProperty(PropertyName = "edges")]
        public IEnumerable<SigmaDataEdge> Edges { get; set; } = new List<SigmaDataEdge>();
    }
}
