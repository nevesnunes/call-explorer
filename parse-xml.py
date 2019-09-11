#!/usr/bin/env python2
# encoding: utf-8

import sys

from BeautifulSoup import BeautifulSoup

if __name__ == "__main__":
    filename = sys.argv[1]
    node = sys.argv[2]
    attr = ''
    if len(sys.argv) == 4:
        attr = sys.argv[3]

    with open(filename) as data:
        soup = BeautifulSoup(data.read())
        if not attr:
            results = [tag.contents for tag in soup.findAll(node)]
        else:
            results = [tag[attr] for tag in soup.findAll(node)]
        for result in results:
            print result
