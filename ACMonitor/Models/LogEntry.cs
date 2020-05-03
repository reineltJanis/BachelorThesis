using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Text;
using System.Text.Json.Serialization;

namespace ACMonitor.Models
{
    public class LogEntry
    {

        [JsonProperty(PropertyName="id")]
        public Guid Id { get; set; } = Guid.NewGuid();
        public string NodeId { get; set; }
        public int Port { get; set; }
        public double State { get; set; }
        public Dictionary<string, double> NeighborStates { get; set; }
        public int Iteration { get; set; }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;

        [Required]
        [JsonProperty(PropertyName="networkId")]
        public string NetworkId { get; set; }
        public double ReferenceSignal { get; set; }
    }
}
