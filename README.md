# toxcrawler
toxcrawler is a [Tox](https://tox.chat) DHT crawler and statistics generator. See it in action at https://toxstats.com/.

## Crawler
The crawler crawls the DHT network with multiple concurrent instances, allowing for a steady stream of up-to-date data on the number of active DHT notes on the network at any given time. When a crawler instance completes its mission, a log file containing all space separated IP addresses that it found is created in the `crawler_logs/{currentdate}/` directory, with the name `{timestamp}.cwl`.

### Compiling
Compile and install the [DHT-addon branch](https://github.com/JFreegman/toxcore/tree/DHT-addon) of toxcore using the given instructions.
Clone this repo to the same base directory as toxcore, then run the command `make` in the `crawler` directory.

## Stats Generator
`crawler_stats.py`, which resides in the `stats/src/` directory, takes all of the log files in `crawler_logs/*`, collects statistics on them, and outputs the results in JSON format in the `stats/` directory. Two JSON files are created: `stats.json` and `raw.json`. The latter should be ignored.

Collected stats include the number of total unique IP's, as well as the number of unique IP's for a specified country, for any given time period, from a year down to any 5 minute interval.

Examples in python:
```python
# prints unique node count for 2016
print jsonObj['2016']['nodes']

# prints unique node count for March 5, 2016
print jsonObj['2016']['03']['05']['nodes']

# prints unique node count for March 5, 2016, between 2100 and 2200 UTC
print jsonObj['2016']['03']['05']['21']['nodes']

# prints unique node count for March 5, 2016, at approximately 2130 UTC
print jsonObj['2016']['03']['05']['21']['30']['nodes']

# prints number of unique nodes originating from Canada for March, 2016
print jsonObj['2016']['03']['geo']['CA']

# prints number of unique nodes originating from the United States for March 5, 2016, at approximately 2145 UTC
print jsonObj['2016']['03']['05']['21']['45']['geo']['US']

# prints timestamp since the last update
print jsonObj['miscStats']['lastUpdate']

#prints timestamp of the oldest entry (i.e. when records begin)
print jsonObj['miscStats']['oldestEntry']

#prints timestamp of the record for most online nodes ever at a given time
print jsonObj['miscStats']['mostOnlineRecord']

```

### Dependencies and Install
You need:
- Python >= 2.7
- pip
- GeoIP
- pytz

For debian-based systems, run the command `sudo apt-get install python-dev libgeoip-dev && pip install GeoIP pytz`
