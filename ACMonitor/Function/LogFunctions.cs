using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Azure.Cosmos;
using ACMonitor.Models;
using System.Collections.Generic;
using System.Threading;
using System.Linq;

namespace ACMonitor.Function
{
    public class LogFunctions
    {
        private Container _logContainer;

        public LogFunctions(CosmosClient cosmosClient)
        {
            _logContainer = cosmosClient.GetDatabase("ACMonitor").GetContainer("Logs");
        }

        [FunctionName("StoreDataStackAsync")]
        public async Task<IActionResult> StoreDataStackAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "log")] HttpRequest req,
            ILogger log)
        {
            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            if (string.IsNullOrWhiteSpace(requestBody))
                return new BadRequestResult();

            List<LogEntry> body;
            try
            {
                body = JsonConvert.DeserializeObject<List<LogEntry>>(requestBody);
            }
            catch (Exception)
            {
                return new BadRequestResult();
            }

            log.LogInformation("Storing " + body?.Count + "elemets.");

            var stack = new LogEntryStack
            {
                LogEntries = body.OrderBy(o => o.Iteration).ToList(),
                NodeId = body.FirstOrDefault().NodeId,
                Timestamp = DateTime.UtcNow,
                NetworkId = body.FirstOrDefault().NetworkId
            };

            await _logContainer.CreateItemAsync(stack);

            return new OkResult();
        }

        [FunctionName("GetData")]
        public IActionResult GetData(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "log/{networkId}/{interval}")] HttpRequest req,
            string networkId,
            int interval,
            ILogger log)
        {
            log.LogInformation("C# HTTP trigger function processed a request.");

            IQueryable<LogEntryStack> orders = _logContainer
                            .GetItemLinqQueryable<LogEntryStack>(allowSynchronousQueryExecution: true, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(networkId) })
                            .Where(o => o.Timestamp >= DateTime.UtcNow.AddSeconds(-interval))
                            .OrderByDescending(o => o.Timestamp);
            var data = orders.ToList();

            return new OkObjectResult(data);
        }
    }
}
