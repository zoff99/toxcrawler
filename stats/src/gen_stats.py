#!/usr/bin/env python

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
