#!/usr/bin/env python

# gen_stats.py
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

import sys
import os

OUT_FILE = "crawler_stats"

class CrawlerStats(object):
    def __init__(self, path):
        self.log_paths = {}  # {'YYYY-mm-dd': ['unixtime1.cwl', 'unixtime2.cwl', ...]}

        log_dirs = next(os.walk(path))
        self.num_days = len(log_dirs)

        if self.num_days < 2:
            return

        base_dir = log_dirs[0]

        for date in log_dirs[1]:
            date_dir = base_dir + date

            for filename in os.listdir(date_dir):
                if date not in self.log_paths:
                    self.log_paths[date] = []

                self.log_paths[date].append(date_dir + '/' + filename)

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print "Usage: gen_stats.py <log_path>"
        sys.exit(1)

    stats = CrawlerStats(sys.argv[1])
