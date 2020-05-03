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

        public static SigmaData ToSigmaData(this IEnumerable<LogEntry> logEntries)
        {
            var data = logEntries.ToList();

            var activeNodes = data.Select(i => i.NodeId);

            var neighborNodes = new SortedSet<string>();
            var edges = new HashSet<Tuple<string, string>>();

            var errorNodes = new SortedSet<string>();

            data.ForEach(i =>
            {
                neighborNodes.UnionWith(i.NeighborStates.Keys);
                edges.UnionWith(
                    i.NeighborStates.Select(
                        ns =>
                        {
                            // for error set
                            data.ForEach(j =>
                            {
                                if (i.Iteration - 1 == j.Iteration && ns.Key.Equals(j.NodeId))
                                {
                                    if (Math.Abs(1 - ns.Value / j.State) > 0.0001){
                                        errorNodes.Add(j.NodeId);
                                        Console.WriteLine($"ERROR ===============================> {j.NodeId}({j.Iteration}): {j.State} <-> {i.State} :({i.Iteration}){ns.Key}");
                                    }
                                }
                            });

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

            var untrackedNeighbors = neighborNodes.Except(activeNodes);

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
                        Y = allNodesList.IndexOf(n) ^ 2,
                        Color = untrackedNeighbors?.Contains(n) == true ? "grey" : (errorNodes.Contains(n) ? "red" : "green")
                    }
                    ).ToList() ?? new List<SigmaDataNode>(),

                Edges = edges.Select(
                    e => new SigmaDataEdge
                    {
                        Source = e.Item1,
                        Target = e.Item2,
                        Color = "grey"
                    }).ToList() ?? new List<SigmaDataEdge>()
            };

            return sigmadata;
        }

    }
}
