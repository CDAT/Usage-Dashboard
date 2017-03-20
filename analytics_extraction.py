from stats.models import LogEvent
from django.utils import timezone
import datetime
import json

n = timezone.now()

one_month = n - datetime.timedelta(30)
three_months = n - datetime.timedelta(90)
six_months = n - datetime.timedelta(180)
one_year = n - datetime.timedelta(365)

# Use these to bucket things
time_boundaries = [one_year, six_months, three_months, one_month]
# first one is "all time",
time_groups = [{}, {}, {}, {}, {}]
finished_groups = []
events = LogEvent.objects.order_by('-session__lastDate')

for e in events:
    country = e.session.netInfo.country
    date = e.session.lastDate
    datestr = "%d-%d-%d" % (date.day, date.month, date.year)
    event = e.action_id
    version = e.source + " " + e.version

    if time_boundaries and e.session.lastDate < time_boundaries[-1]:
        time_boundaries.pop()
        finished_groups.append(time_groups.pop())

    for g in time_groups:
        geo = g.get("geo", {})
        c = geo.get(country, {})
        action = c.get("action", {})
        count = action.get(event, 0)
        count += e.frequency
        action[event] = count
        c["action"] = action
        geo[country] = c

        time = g.get("timeseries", {})
        d = time.get(datestr, {})
        v = d.get("action", {})
        count = v.get(event, 0)
        v[event] = count + e.frequency
        d["action"] = v
        time[datestr] = d
        g["timeseries"] = time

        histo = g.get("histo", {})
        v = histo.get("action", {})
        count = v.get(event, 0)
        v[event] = count + e.frequency
        histo["action"] = v
        g["histo"] = histo

finished_groups.append(time_groups.pop())
files = ["30_days.json", "60_days.json", "90_days.json", "180_days.json", "365_days.json", "all.json"]
for g, f in zip(finished_groups, files):
    with open(f, "w") as outfile:
        json.dump(g, f)
