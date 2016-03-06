#!/usr/bin/env python

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
import copy
import time
from datetime import datetime

import GeoIP
gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

# crawler logs base directory
CRAWLER_LOGS_DIRECTORY = '../../crawler_logs'

# The json file we generate for outside use, which does not include IP caches
STATS_FULL_FILENAME = '../stats.json'

# The json file we read from and write to which includes all IP caches
STATS_FILENAME = '../raw.json'

# Smallest time unit (in Ms) for which to store stats
TIMETICK_INTERVAL = 5

"""
Returns the closest timetick to M, rounded down. e.g. lowestTimeTick(11) == 10, lowestTimeTick(19) == 15
"""
def lowestTimeTick(minute):
    return minute - (minute % TIMETICK_INTERVAL)

class CrawlerStats(object):
    def __init__(self):
        self.json = None
        self.jsonNoIPs = None
        self.statsObj = self.generateStats()

    """
    getJson() and getJsonNoIPs() return json representations of the stats object,
    the former with IP caches intact and the latter without.

    WARNING: These functions call generateJson() which deletes all IP caches from the statsObj.
    """
    def getJson(self):
        if not self.json:
            self.generateJson()

        return self.json

    def getJsonNoIPs(self):
        if not self.jsonNoIPs:
            self.generateJson()

        return self.jsonNoIPs

    """
    Generates two json objects, one with IP caches and one without.
    """
    def generateJson(self):
        self.json = json.dumps(self.statsObj)
        self.removeIPs(self.statsObj)
        self.jsonNoIPs = json.dumps(self.statsObj)

    """
    Puts all log files with a more recent timetsamp than lastUpdate in self.logs
    """
    def getLogDirectories(self, lastUpdate):
        log_dirs = next(os.walk(CRAWLER_LOGS_DIRECTORY))

        if len(log_dirs) < 2:
            return

        L = []
        base_dir = log_dirs[0]
        for date in log_dirs[1]:
            date_dir = base_dir + '/' + date
            for filename in os.listdir(date_dir):
                ts = filename.split('.cwl')[0]
                if filename[-4:] == '.cwl' and int(ts) > lastUpdate:
                    L.append(date_dir + '/' + filename)

        return L

    """
    Creates an object containing statistics retreived from crawler logs.
    """
    def generateStats(self):
        statsObj = {}

        # Try to load json file from disk if it exists,
        try:
            fp = open(STATS_FILENAME, 'r').read().strip()
            try:
                statsObj = json.loads(fp)
            except ValueError:
                pass
        except IOError:
            pass

        lastUpdate, mostRecent, oldest = 0, 0, 99999999999

        if 'lastUpdate' in statsObj:
            lastUpdate = statsObj['lastUpdate']

        if 'oldestEntry' in statsObj:
            oldest = statsObj['oldestEntry']

        logs = self.getLogDirectories(lastUpdate)

        for file in logs:
            ts = int(file[max((file.rfind('/'), 0)) + 1 : file.rfind('.')])  # extract timestamp from path
            Y, m, d, H, M = datetime.fromtimestamp(ts).strftime("%Y-%m-%d-%H-%M").split('-')
            tick = str(lowestTimeTick(int(M)))
            IPlist, numIPs = self.getIPList(file)

            if numIPs < 100:
                continue

            if ts < oldest:
                oldest = ts
                statsObj['oldestEntry'] = ts

            if ts > mostRecent:
                mostRecent = ts
                statsObj['lastUpdate'] = ts

            if ts <= lastUpdate:
                continue

            if Y not in statsObj:
                statsObj[Y] = {"nodes": 0, "geo": {}, "IPs": {}}
            if m not in statsObj[Y]:
                statsObj[Y][m] = {"nodes": 0, "geo": {}, "IPs": {}}
            if d not in statsObj[Y][m]:
                statsObj[Y][m][d] = {"nodes": 0, "geo": {}, "IPs": {}}
            if H not in statsObj[Y][m][d]:
                statsObj[Y][m][d][H] = {"nodes": 0, "geo": {}, "IPs": {}}
            if tick not in statsObj[Y][m][d][H]:
                statsObj[Y][m][d][H][tick] = {"nodes": 0, "geo": {}}

            # average results for all minutes in a given timetick interval
            n = statsObj[Y][m][d][H][tick]['nodes']
            statsObj[Y][m][d][H][tick]['nodes'] = ((n + numIPs) / 2) if n else numIPs

            for ip in IPlist:
                self.doIPStats(ip, statsObj[Y])
                self.doIPStats(ip, statsObj[Y][m])
                self.doIPStats(ip, statsObj[Y][m][d])
                self.doIPStats(ip, statsObj[Y][m][d][H])
                self.incrementCountry(ip, statsObj[Y][m][d][H][tick]['geo'])

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
    Increments the country counter in obj for given ip address
    """
    def incrementCountry(self, ip, obj):
        if (not ip) or (ip[0] == '['):    # pygeoip doesn't support ipv6
            return

        country = gi.country_code_by_addr(ip)
        obj[country] = obj.get(country, 0) + 1

    """
    Removes all IP entries from from obj's IP cache
    """
    def removeIPs(self, obj):
        for key in obj:
            if key == 'IPs':
                obj['IPs'] = {}
            if isinstance(obj[key], dict):
                self.removeIPs(obj[key])   # I wonder if this sweet recursion will work forever


if __name__ == '__main__':
    start = time.time()

    print "Collecting stats..."
    stats = CrawlerStats()

    print "Generating " + STATS_FULL_FILENAME
    outfile = open(STATS_FULL_FILENAME, 'w')
    jsonNoIps = stats.getJsonNoIPs()
    outfile.write(jsonNoIps)

    print "Generating " + STATS_FILENAME
    outfile = open(STATS_FILENAME, 'w')
    json = stats.getJson()
    outfile.write(json)

    end = time.time()

    print "Finished in " + str(end - start) + " seconds"
