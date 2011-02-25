#!/usr/bin/env python
import beanstalkc
import pprint

b = beanstalkc.Connection()

print "Overall Stats:"
for key, val in sorted(b.stats().items()):
    print "{0:>30} {1}".format(key, val)

print
print "Tubes:"
for tube in b.tubes():
    print "=====", tube, "====="
    for key, val in sorted(b.stats_tube(tube).items()):
        print "{0:>30} {1}".format(key, val)
