#!/usr/bin/env python2

# crawler_stats.py
#
#
#  Copyright (C) 2016 toxcrawler All Rights Reserved.
#
#  This file is part of toxcrawler.
#
#  toxcrawler is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  toxcrawler is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with toxcrawler.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import urllib
import time
import pytz
from sys import argv, exit
from datetime import datetime

import GeoIP
gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

# crawler logs base directory
CRAWLER_LOGS_DIRECTORY = '../../crawler_logs'

# The json file we generate for outside use, which does not include IP caches
STATS_FULL_FILENAME = '../stats.json'

# The json file we read from and write to which includes all IP caches
STATS_FILENAME = '../raw.json'

TEMP_FILE_EXT = '.tmp'

# Smallest time unit (in minutes) for which to store stats
TIMETICK_INTERVAL = 5

# Key for unknown geolocations
UNKNOWN_COUNTRY = '??'

"""
Returns the closest timetick to minute, rounded down. e.g. lowestTimeTick(11) == 10, lowestTimeTick(19) == 15
"""
def lowestTimeTick(minute):
    return minute - (minute % TIMETICK_INTERVAL)

"""
Removes all IP entries from from obj's IP caches
"""
def removeIPs(obj):
    for key in obj:
        if key == 'IPs':
            obj['IPs'] = {}
        elif isinstance(obj[key], dict):
            removeIPs(obj[key])   # I wonder if this sweet recursion will work forever

class CrawlerStats(object):
    def __init__(self, do_cleanup=False):
        self.statsObj = self.generateStats(do_cleanup)

    def getStatsObj(self):
        return self.statsObj

    """
    Returns a list containing all files from the logs directory
    with a more recent timetsamp than lastUpdate.
    """
    def getLogDirectories(self, lastUpdate):
        log_dirs = next(os.walk(CRAWLER_LOGS_DIRECTORY))

        if len(log_dirs) < 2:
            return []

        L = []
        base_dir = log_dirs[0]

        for date in log_dirs[1]:
            date_dir = base_dir + '/' + date
            for filename in os.listdir(date_dir):
                if filename[-4:] == '.cwl' and int(filename[:-4]) > lastUpdate:
                    L.append(date_dir + '/' + filename)

        return L

    """
    Creates an object containing statistics retreived from crawler logs.
    If cleanup is set to True, this function will delete superfluous logs from
    the crawler_logs directory, meaning only one log file per TIMETICK_INTERVAL is retained.
    """
    def generateStats(self, do_cleanup=False):
        statsObj = { 'miscStats': {'lastUpdate': 0, 'oldestEntry': 99999999999, 'mostOnlineRecord': [0, 0]} }
        cleanup = []

        # Try to load json file from disk if it exists,
        try:
            fp = open(STATS_FILENAME, 'r').read().strip()
            try:
                statsObj = json.loads(fp)
            except ValueError:
                pass
        except IOError:
            pass

        miscStatsObj = statsObj['miscStats']
        lastUpdate = miscStatsObj['lastUpdate']
        logs = self.getLogDirectories(lastUpdate)
        last_tick = ""

        for file in logs:
            ts = int(file[max((file.rfind('/'), 0)) + 1 : file.rfind('.')])  # extract timestamp from path
            Y, m, d, H, M = datetime.fromtimestamp(ts, tz=pytz.utc).strftime("%Y %m %d %H %M").split()
            tick = "%02d" % lowestTimeTick(int(M))

            sameTick = tick == last_tick
            if do_cleanup and sameTick:
                cleanup.append(file)
                last_tick = tick
                continue

            last_tick = tick
            IPlist, numIPs = self.getIPList(file)

            if numIPs < 100:
                continue

            if ts < miscStatsObj['oldestEntry']:
                miscStatsObj['oldestEntry'] = ts

            if ts > miscStatsObj['lastUpdate']:
                miscStatsObj['lastUpdate'] = ts

            if ts <= lastUpdate:
                continue

            if numIPs > miscStatsObj['mostOnlineRecord'][1]:
                miscStatsObj['mostOnlineRecord'][0] = ts
                miscStatsObj['mostOnlineRecord'][1] = numIPs

            newTick = True

            if Y not in statsObj:
                statsObj[Y] = {"nodes": 0, "geo": {}, "IPs": {}}
            if m not in statsObj[Y]:
                statsObj[Y][m] = {"nodes": 0, "geo": {}, "IPs": {}}
            if d not in statsObj[Y][m]:
                statsObj[Y][m][d] = {"nodes": 0, "geo": {}, "IPs": {}}
            if H not in statsObj[Y][m][d]:
                statsObj[Y][m][d][H] = {"nodes": 0, "geo": {}, "IPs": {}}
            if tick not in statsObj[Y][m][d][H]:
                statsObj[Y][m][d][H][tick] = {"nodes": numIPs, "geo": {}}
            else:
                newTick = False

            # average results for all minutes in a given timetick interval
            n = statsObj[Y][m][d][H][tick]['nodes']
            statsObj[Y][m][d][H][tick]['nodes'] = ((n + numIPs) / 2) if n else numIPs

            for ip in IPlist:
                self.doIPStats(ip, statsObj[Y])
                self.doIPStats(ip, statsObj[Y][m])
                self.doIPStats(ip, statsObj[Y][m][d])
                self.doIPStats(ip, statsObj[Y][m][d][H])

                if newTick:
                    self.incrementCountry(ip, statsObj[Y][m][d][H][tick]['geo'])

        for file in cleanup:
            os.remove(file)

        return statsObj

    """
    Returns a tuple containing a list of all IP addresses found in logfile, and the length of the list.
    """
    def getIPList(self, logfile):
        IPlist = set(open(logfile, 'r').read().strip().split(' '))
        return IPlist, len(IPlist)

    """
    Checks IP for uniqueness and increments relevant counters in obj.
    """
    def doIPStats(self, ip, obj):
        if ip not in obj['IPs']:
            obj['nodes'] += 1
            obj['IPs'][ip] = 1
            self.incrementCountry(ip, obj['geo'])

    """
    Increments the country counter in obj for given ip address.
    """
    def incrementCountry(self, ip, obj):
        country = gi.country_code_by_addr(ip)
        if not country:
            country = UNKNOWN_COUNTRY

        obj[country] = obj.get(country, 0) + 1

if __name__ == '__main__':
    start = time.time()

    print "Collecting stats..."
    stats = CrawlerStats(True) if (len(argv) > 1 and argv[1].lower() == 'cleanup') else CrawlerStats()

    statsObj = stats.getStatsObj()

    if not statsObj:
        print "Empty stats object"
        exit(1)

    # Dump full data including IP addresses to raw json object
    fp1 = open(STATS_FILENAME + TEMP_FILE_EXT, 'w')
    fp1.write(json.dumps(statsObj))
    os.rename(STATS_FILENAME + TEMP_FILE_EXT, STATS_FILENAME)

    # Dump data without IP addresses
    removeIPs(statsObj)
    fp2 = open(STATS_FULL_FILENAME + TEMP_FILE_EXT, 'w')
    fp2.write(json.dumps(statsObj))
    os.rename(STATS_FULL_FILENAME + TEMP_FILE_EXT, STATS_FULL_FILENAME)

    end = time.time()

    print "Finished in " + str(end - start) + " seconds"
