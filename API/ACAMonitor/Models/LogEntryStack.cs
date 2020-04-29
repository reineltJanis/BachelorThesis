using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace ACAMonitor.Models
{
    public class LogEntryStack
    {
        [JsonProperty(PropertyName = "id")]
        public Guid Id { get; set; } = Guid.NewGuid();
        [JsonProperty(PropertyName = "nodeId")]
        public string NodeId { get; set; }
        [JsonProperty(PropertyName = "timestamp")]
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
        [JsonProperty(PropertyName = "logEntries")]
        public List<LogEntry> LogEntries { get; set; }
        [JsonProperty(PropertyName = "networkId")]
        public string NetworkId { get; set; }
    }
}
