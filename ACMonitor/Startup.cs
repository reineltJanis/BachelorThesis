using Microsoft.Azure.Cosmos.Fluent;
using Microsoft.Azure.Functions.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using System;
using System.Threading;
using Microsoft.Azure.Cosmos;

[assembly: FunctionsStartup(typeof(ACMonitor.Startup))]
namespace ACMonitor
{
    public class Startup : FunctionsStartup
    {
        public override void Configure(IFunctionsHostBuilder builder)
        {
            builder.Services.AddLogging(loggingBuilder =>
            {
                loggingBuilder.AddFilter(level => true);
            });

            builder.Services.AddSingleton(s =>
            {
                CosmosClientBuilder builder = new CosmosClientBuilder(Environment.GetEnvironmentVariable("ConnectionStrings:CosmosDBConnectionString"));
                var client = builder.WithConnectionModeDirect()
                .WithBulkExecution(true)
                .Build();

                client.CreateDatabaseIfNotExistsAsync("ACMonitor").Wait();
                var db = client.GetDatabase("ACMonitor");
                db.CreateContainerIfNotExistsAsync(new ContainerProperties{ PartitionKeyPath="/networkId", DefaultTimeToLive=1200, Id="Logs"}).Wait();

                return client;
            });
        }
    }
}