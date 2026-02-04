import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

def compute_exo_difficulty(exo_push_count):
    max_ = max(exo_push_count.values()) if exo_push_count else 1
    diffs = {k: v / max_ for k, v in exo_push_count.items()}
    return diffs

def get_exo_data(PARAMS):
    time_max = PARAMS["time_max_hours"]

    exo_day_times = defaultdict(list)
    exo_push_count = defaultdict(int)

    for filename in os.listdir(PARAMS["data_dir"]):
        if not filename.endswith(".json"):
            continue

        with open(os.path.join(PARAMS["data_dir"], filename), "r") as f:
            data = json.load(f)

        for ex, category in data.items():
            for info in category["tags"].values():
                date_str = info.get("submission_date")
                t = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                hour_in_day = t.hour + t.minute / 60.0
                delta_hours = (t - PARAMS["first_day"]).total_seconds() / 3600.0

                if PARAMS["window_start"] <= hour_in_day <= PARAMS["window_end"] and delta_hours <= time_max:
                    exo_push_count[ex] += 1
                    exo_day_times[(ex, t.date())].append(hour_in_day - PARAMS["window_start"])

    diffs = compute_exo_difficulty(exo_push_count)
    return exo_day_times, diffs
