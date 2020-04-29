using Newtonsoft.Json.Converters;
using System;
using System.Text.Json.Serialization;

namespace ACMonitor.Models
{
    public class LogEntryStackDocument : LogEntryStack
    {
        public int _ttl { get; set; }
        [JsonConverter(typeof(UnixDateTimeConverter))]
        public DateTime _ts { get; set; }
    }
}
