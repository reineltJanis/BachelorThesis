# Visualization of Average Consensus Algrorithms in Distributed Systems
## ACNetwork
Developed in Ubuntu 18.04 LTS with Python. Creates a network simulation of average consensus agents. Theses agents can call the **ACMonitor** API.

## ACMonitor
Receives and stores logs to a CosmosDB Account. The API then converts the data to analyzed data which can be displayed using the JavaScript projects Sigma Js and Plotly Js for visualization.

## Webpage
Contains a sample HTML document to simulate a calling of the API and a visualization of the data with Sigma Js and Plotly Js.
