#!/usr/bin/python
import argparse
import datetime as dt
import itertools
import json
import os
import statistics

import matplotlib.pyplot as plot

from nlp_pipeline.settings import LOGS_DIR

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", default=LOGS_DIR, help="The Log file", type=str)
    parser.add_argument("-s", "--start", default=None, help="Start timestamp")

    args = parser.parse_args()

    counts = {}
    times = {}
    marker = itertools.cycle((",", "+", ".", "o", "*", "p", "^"))
    for filename in os.listdir(args.file):
        with open(os.path.join(args.file, filename), "r") as f:  # open in readonly mode
            for record in f:
                record = json.loads(record)
                try:
                    if not counts.get(record["task"]["name"], None):
                        counts[record["task"]["name"]] = []
                        times[record["task"]["name"]] = []

                    if record["runtime"] is not None and record["task"]["name"] != "Directory Reader":
                        counts[record["task"]["name"]].append(record["runtime"])
                        times[record["task"]["name"]].append(record["timestamp"])
                except Exception:  # nosec B112
                    continue

    for key, items in counts.items():
        try:
            print(
                f"Task {key}: [ Avg {statistics.mean(items):.2f}s ] - [ Median {statistics.median(items):.2f}s ] - [ Min {min(items):.2f} ] -  [ Max {max(items):.2f} ] "
            )
            converted_dates = list(map(dt.datetime.strptime, times[key], len(times[key]) * ["%Y-%m-%d %H:%M:%S,%f"]))
            plot.scatter(converted_dates, items, label=key, marker=next(marker))
        except Exception:  # nosec
            continue

    plot.tick_params(
        axis="x",  # changes apply to the x-axis
        which="both",  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False,
    )  # labels along the bottom edge are off

    plot.title("Celery timeseries run [ 8 workers ] & [ 1150 files ]")
    plot.xlabel("Timeseries")
    plot.ylabel("Task Runtime (seconds)")
    plot.legend()
    plot.show()
