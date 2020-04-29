using ACMonitor.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace ACMonitor.Extensions
{
    static class SigmaDataExtension
    {

        public static SigmaData ToSigmaData(this IQueryable<LogEntry> logEntryPosts)
        {
            return logEntryPosts.ToList().ToSigmaData();
        }

        public static SigmaData ToSigmaData(this IEnumerable<LogEntry> logEntryPosts)
        {
            var data = logEntryPosts.ToList();

            var activeNodes = data.Select(i => i.NodeId);

            var neighborNodes = new SortedSet<string>();
            var edges = new HashSet<Tuple<string, string>>();
            data.ForEach(i =>
            {
                neighborNodes.UnionWith(i.NeighborStates.Keys);
                edges.UnionWith(
                    i.NeighborStates.Select(
                        ns =>
                        {
                            var lst = new List<string>();
                            lst.Add(i.NodeId);
                            lst.Add(ns.Key);
                            lst.Sort();
                            return Tuple.Create(lst[0], lst[1]);
                        }
                        )
                    .ToList());
            });

            var allNodes = new SortedSet<string>();
            allNodes.UnionWith(activeNodes);
            allNodes.UnionWith(neighborNodes);

            var allNodesList = allNodes.ToList();

            var rand = new Random();

            var sigmadata = new SigmaData
            {
                Nodes = allNodes.Select(
                    n => new SigmaDataNode
                    {
                        Id = n,
                        Label = n,
                        Size = edges.Where(e => (e.Item1 == n || e.Item2 == n)).Count() * 3,
                        X = allNodesList.IndexOf(n),
                        Y = allNodesList.IndexOf(n) ^ 2
                    }
                    ).ToList() ?? new List<SigmaDataNode>(),

                Edges = edges.Select(
                    e => new SigmaDataEdge
                    {
                        Source = e.Item1,
                        Target = e.Item2
                    }).ToList() ?? new List<SigmaDataEdge>()
            };

            return sigmadata;
        }

        

        //private string DetermineColor(List<LogEntryStack> allStacks)
        //{
        //    var logEntries = allStacks
        //        .SelectMany(an => an.LogEntries)
        //        .ToList();

        //    var singleNodes = logEntries
        //        .GroupBy(le => le.NodeId);

        //    var neighborStates = logEntries
        //        .SelectMany(le => le.NeighborStates);

        //    logEntries.GroupBy(le => le.Iteration).ToList().ForEach(it =>
        //    {
        //        it.ToList()
        //        .SelectMany(o => o.NeighborStates)
        //                .Where(o => !singleNodes.Any(r => singleNodes.Any(single => single.Key == o.Key) ))
        //                .ToList()
        //                .Select(o =>
        //                {
        //                    singleNodes.Add(new AnalyzedDataEntryRawData { NodeId = o.Key, State = o.Value, ReferenceSignal = null });
        //                    return new AnalyzedDataEntryFlagData { FromNode = o.Key, ErrorType = AnalyzedDataEntryFlagData.MISSING_NODE };
        //                });
        //    });
                        
        //}
    }
}
