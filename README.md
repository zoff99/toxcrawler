# toxcrawler
toxcrawler is a [Tox](https://tox.chat) DHT network crawler.

## Crawler
The crawler crawls the DHT network with multiple concurrent instances, allowing for a steady stream of up-to-date data on the number of active DHT notes on the network at any given time. When a crawler instance completes its mission, a log file containing all space separated IP addresses that it found is created in the `crawler_logs/{currentdate}/` directory, with the name `{timestamp}.cwl`.

### Compiling
Compile and install [toxcore](https://github.com/toktok/c-toxcore).
Clone this repo to the same base directory as toxcore, then run the command `make` in the `crawler` directory.
