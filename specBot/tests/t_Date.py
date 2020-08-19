#!/usr/bin/python3

import os
import sys

sys.path = [".", ".."] + [os.path.dirname(os.path.abspath(sys.argv[0]))] + sys.path

from Date import Date


# test Date.nextDayMidnight()

pairs = [
	["1970-01-01 17:40", "1970-01-02"],
	["2016-02-29", "2016-03-01"],
	["2018-12-31 23:59:59", "2019-01-01"],
	["2016-08-15 03:19", "2016-08-16"],
]

for p in pairs:
	d0 = Date(p[0])
	d1 = Date(p[1])

	d = d0.nextDayMidnight()

	if not d.same(d1): raise Exception("Date.nextDayMidnight() gives incorrect results %s, %s" % (d, d1))


# Test initialization from a Date object


ts = ["1970-01-01 17:40", "1970-01-02",
"2016-02-29", "2016-03-01",
"2018-12-31 23:59:59", "2019-01-01",
"2016-08-15 03:19", "2016-08-16"]

for t in ts:
	d0 = Date(t)
	d = Date(d0)

	if not d0.same(d): raise Exception("Date object initialized from another Date object carries the wrong date")


# Test Date.same()

ts = ["1970-01-01 17:40", "1970-01-02",
"2016-02-29", "2016-03-01",
"2018-12-31 23:59:59", "2019-01-01",
"2016-08-15 03:19", "2016-08-16",
"2016-08-15 03:19", "2016-08-15 03:19:01"]

# equal
for t in ts:
	d0 = Date(t)
	d1 = Date(t)
if not d0.same(d1): raise Exception("Date.same() gives incorrect results on equal dates")

# unequal
for t in ts:
	d0 = Date(t)
	for tt in ts:
		if t == tt: continue
		d1 = Date(tt)
		if d0.same(d1): raise Exception("Date.same() gives incorrect results on unequal dates d0=%s, d1=%s; t=%s; tt=%s" % (d0, d1, t, tt))

# A test for Date.__lt__ and others

dst = [
	"2015-01-01",
	"2015-01-01 00:00:01",
	"2016-01-01",
	"2016-02-29",
	"2016-03-01",
	"2016-03-05 02:05",
	"2016-04-05 02:05",
	"2016-04-07 02:05",
	"2016-04-07 02:05:01",
	"2016-04-07 02:06",
	"2018-04-05 02:05",
]

ds = list(Date(d) for d in dst)

for i in range(len(ds)):
	d = ds[i]
	for j in range(i, len(ds)):
		dd = ds[j]
		if j > i  and  not ( dd > d): raise Exception("Date.__gt__() gives incorrect results")
		if j > i  and  not ( d < dd): raise Exception("Date.__lt__() gives incorrect results")
		if not ( dd >= d): raise Exception("Date.__ge__() gives incorrect results")
		if not ( d <= dd): raise Exception("Date.__le__() gives incorrect results")

# fractional and negative time differences

d1 = Date("2018-01-01 00:00:00")
d2 = Date("2018-01-01 00:00:15")

m = d1.minutesEarlier(d2)
if abs(m - 0.25) > 1e-10: raise Exception("Date.minutesEarlier() cannot deal with fractional minutes")

m = d2.minutesEarlier(d1)
if abs(m + 0.25) > 1e-10: raise Exception("Date.minutesEarlier() cannot deal with negative time differences")
