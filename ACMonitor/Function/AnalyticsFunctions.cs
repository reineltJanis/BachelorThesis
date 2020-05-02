using ACMonitor.Extensions;
using ACMonitor.Models;
using ACMonitor.Services;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Cosmos;
using Microsoft.Azure.Cosmos.Linq;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace ACMonitor.Function
{
    public class AnalyticsFunctions
    {
        private Container _logContainer;

        public AnalyticsFunctions(
            CosmosClient cosmosClient
            )
        {
            _logContainer = cosmosClient
                .GetDatabase("ACMonitor")
                .GetContainer("Logs");
        }


        [FunctionName("AnalyzeDataAsync")]
        public async Task<IActionResult> AnalyzeDataAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "analytics/plotly/{networkId}/{interval}")] HttpRequest req,
            string networkId,
            int interval,
            ILogger log)
        {
            string body = await new StreamReader(req.Body).ReadToEndAsync();
            Dictionary<string, int> continueAtIteration;
            try
            {
                continueAtIteration = JsonConvert.DeserializeObject<Dictionary<string, int>>(body);
            }
            catch (Exception)
            {
                return new BadRequestResult();
            }

            if (continueAtIteration == null)
                continueAtIteration = new Dictionary<string, int>();

            var query = _logContainer
                .GetItemLinqQueryable<LogEntryStack>(allowSynchronousQueryExecution: true, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(networkId) })
                .Where(o => o.Timestamp >= DateTime.UtcNow.AddSeconds(-interval));

            var iterator = query.ToFeedIterator();

            var documents = new List<LogEntryStack>();

            while (iterator.HasMoreResults)
            {
                documents.AddRange((await iterator.ReadNextAsync()).ToList());
            }

            if (documents.Count <= 0)
                return new OkObjectResult(new { data = new List<PlotyTrace>(), lastIteration = continueAtIteration, statistics = new List<PlotyTrace>() });

            var logEntries = documents
                .SelectMany(o => o.LogEntries)
                .Where(o => o.Iteration > (continueAtIteration.ContainsKey(o.NodeId) ? continueAtIteration[o.NodeId] : -1))
                .ToList();

            var traces = logEntries
                .OrderBy(o => o.Iteration)
                .GroupBy(o => o.NodeId)
                .Select(o => new PlotyTrace { name = o.Key, x = o.ToList().Select(k => (double)k.Iteration).ToList(), y = o.ToList().Select(s => s.State).ToList(), line = new PlotTraceLine { width = 1 }, type = "scatter" })
                .ToList();

            // var averages = logEntries
            //     .Where(o => o.Iteration <= traces.Select(t => t.x.Max()).Min())
            //     .Where(o => o.Iteration > (continueAtIteration.ContainsKey("average") ? continueAtIteration["average"] : -1))
            //     .GroupBy(o => o.Iteration)
            //     .OrderBy(o => o.Key)
            //     .Select(o => Tuple.Create((double)o.Key, o.ToList().Select(s => s.ReferenceSignal).ToList().Average()))
            //     .ToList();

            var maxIterations = continueAtIteration;
            traces
                .ForEach(t => maxIterations[t.name] = (int)t.x.Max());

            var statistics = documents
                .SelectMany(o => o.LogEntries)
                // .Where(o => o.Iteration < traces.Select(t => KeyValuePair.Create(t.name, (int)t.x.Max())).Union(continueAtIteration.Where(h => h.Key!="average")).Min(t => t.Value))
                .Where(o => o.Iteration <= maxIterations.Where(t => t.Key != "average").Min(t => t.Value))
                .Where(o => o.Iteration > (continueAtIteration.ContainsKey("average") ? continueAtIteration["average"] : -1))
                .GroupBy(o => o.Iteration)
                .OrderBy(o => o.Key)
                .Select(o =>
                {
                    var avgRef = o.ToList().Select(s => s.ReferenceSignal).ToList().Average();
                    var avgState = o.ToList().Select(s => s.State).ToList().Average();
                    var maxState = o.ToList().Max(d => d.State);
                    var minState = o.ToList().Min(d => d.State);
                    var convergenceIterations = documents
                    .SelectMany(c => c.LogEntries)
                    .Where(c => c.Iteration >= o.Key - 2 && c.Iteration <= o.Key + 1) // range for required states
                    .GroupBy(c => c.NodeId)
                    .Where(c => c.ToList().Count == 4) // enough items in to calculate
                    .Where(c => Math.Abs(c.ToList().Max(z => z.ReferenceSignal) - c.ToList().Min(z => z.ReferenceSignal)) < 0.001) // noch change in ref
                    .Select(c => new
                    {
                        NodeID = c.Key,
                        ConvergenceRate = StatisticCalculator.CalculateConvergenceRate(
                            c.ToList()
                            .OrderBy(x => x.Iteration)
                            .Select(x => x.State)
                            .ToArray())
                    })
                    .ToList();
                    return new
                    {
                        Iteration = o.Key,
                        Average = avgRef,
                        Error = StatisticCalculator.CalculatePercentError(avgState, avgRef),
                        Difference = Math.Abs(maxState) + Math.Abs(minState) > 0 ? StatisticCalculator.CalculatePercentDifferencePeak(o.ToList().Select(r => r.State).ToArray()) : 0,
                        ConvergenceRate = convergenceIterations.Count > 0 ? convergenceIterations.Average(c => c.ConvergenceRate) : double.NaN
                    };
                })
                .ToList();
            if (statistics.Count > 0)
                traces.Insert(0, new PlotyTrace
                {
                    name = "average",
                    x = statistics.Select(o => (double)o.Iteration).ToList(),
                    y = statistics.Select(o => o.Average).ToList()
                });

            var lastIterations = continueAtIteration;
            traces.ForEach(o => lastIterations[o.name] = (int)o.x.Max());


            var statisticTraces = new List<PlotyTrace>();
            statisticTraces.Add(new PlotyTrace
            {
                name = "%Error",
                x = statistics.Where(s => s.Error.HasValue).Select(s => (double)s.Iteration).ToList(),
                y = statistics.Where(s => s.Error.HasValue).Select(s => s.Error.Value).ToList()
            });

            statisticTraces.Add(new PlotyTrace
            {
                name = "%Difference",
                x = statistics.Select(s => (double)s.Iteration).ToList(),
                y = statistics.Select(s => s.Difference).ToList()
            });

            statisticTraces.Add(new PlotyTrace
            {
                name = "Convergence",
                x = statistics.Where(s => !double.IsNaN(s.ConvergenceRate)).Select(s => (double)s.Iteration).ToList(),
                y = statistics.Where(s => !double.IsNaN(s.ConvergenceRate)).Select(s => s.ConvergenceRate).ToList()
            });


            var result = new
            {
                data = traces,
                statistics = statisticTraces,
                lastIterations = lastIterations
            };

            return new OkObjectResult(result);

        }


        [FunctionName("GetGraph")]
        public IActionResult GetGraph(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "analytics/sigma/{networkId}/{interval}")] HttpRequest req,
            string networkId,
            int interval,
            ILogger log)
        {
            log.LogInformation("GetGraph function processed a request.");

            try
            {
                var query = _logContainer
                    .GetItemLinqQueryable<LogEntryStack>(allowSynchronousQueryExecution: true, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(networkId) })
                    .Where(o => o.Timestamp >= DateTime.UtcNow.AddSeconds(-interval))
                    .ToList();
                if (query?.Count > 0)
                    return new OkObjectResult(query.SelectMany(s => s.LogEntries).ToSigmaData());
                else
                    return new OkObjectResult(new SigmaData { });
            }
            catch (ArgumentNullException)
            {
                return new OkObjectResult(new SigmaData { });
            }
        }

    }
}
