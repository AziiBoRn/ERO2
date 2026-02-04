from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import pickle
from collections import Counter

from pushs.build_exo_times import get_exo_data
from pushs.generation_prepa import generate_pushes_prepa
from pushs.generation_ing import generate_pushes_ing

def plot_pushes(pushes, prepa=False):
    timestamps = [datetime.fromisoformat(p.time.isoformat()) for p in pushes]

    timestamps_minute = [dt.replace(second=0, microsecond=0) for dt in timestamps]
    counts = Counter(timestamps_minute)

    sorted_times = sorted(counts.keys())
    push_counts = [counts[t] for t in sorted_times]

    plt.figure(figsize=(15, 6))
    plt.bar(sorted_times, push_counts, width=0.005 if prepa else 0.004, alpha=0.7)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.gcf().autofmt_xdate(rotation=45)
    plt.xlabel("Datetime")
    plt.ylabel("Number of pushs / min")
    plt.title("Nombre of pushs / min")
    plt.tight_layout()
    plt.savefig("results/tags_prepa.png" if prepa else "results/tags_ing.png", dpi=200)
    #plt.show()

PARAMS_SCRAPPER = {
    "data_dir": "../Scrapper",
    "window_start": 14,
    "window_end": 24,
    "first_day": datetime(2023, 10, 2, 0, 0, 0),
    "time_max_hours": 24 * 15
}

PARAMS_ING = {
    "window_start": 14,
    "window_end": 24,
    "population_size": 600,
    "percentage_strong": 0.1,
    "nb_points_per_hour": 12,
    "gamma_strong": {"base_mean": 1.0, "max_mean": 8.0},
    "gamma_normal": {"base_mean": 2.0, "max_mean": 12.0},
    "gamma_shape": 2.0,
    "jitter_hours": 0
}

PARAMS_PREPA = {
    "population_size": 1500,
    "nb_weeks": 2,
    "start_date": datetime(2023, 10, 2, 0, 0, 0),
    "mean_pushes_per_student": 5,
    "week_weights": {0: 0.15, 1: 0.025, 2: 0.025, 3: 0.05, 4: 0.25, 5: 0.15, 6: 0.35},
    "daily_distributions": {
        "weekday": {
            "t_student": {"df": 3, "scale": 3, "peak_hour": 22},
            "exponential": {"scale": 3, "weight": 0.1}
        },
        "weekend": {
            "t_student": {"df": 3, "scale": 3, "peak_hour": 22},
            "exponential": {"scale": 3, "weight": 0.1}
        }
    },
    "time_resolution_min": 5
}

CACHE_FILE = "pushes_cache.pkl"

def generate_pushes():
    # Get exo datas
    print("Compute stats from scrapper...")
    exo_day_times, diffs = get_exo_data(PARAMS_SCRAPPER)

    print("Generate ING tags...")
    ing = generate_pushes_ing(PARAMS_ING, exo_day_times, diffs)
    print("Total ING tags:", len(ing))

    print("Generate PREPA tags...")
    prepa = generate_pushes_prepa(PARAMS_PREPA)
    print("Total PREPA tags:", len(prepa))

    plot_pushes(ing)
    plot_pushes(prepa, True)

    return ing + prepa

def generate_pushes_cached(invalidate=False):
    file = CACHE_FILE + "_" + str(PARAMS_ING["percentage_strong"])

    if not invalidate and os.path.exists(file):
        print(f"Loading pushes from cache: {file}")
        with open(file, "rb") as f:
            pushes = pickle.load(f)
        print(f"Loaded {len(pushes)} pushes from cache.")
        return pushes

    print("Cache not found, generating pushes...")
    pushes = generate_pushes()

    with open(file, "wb") as f:
        pickle.dump(pushes, f)
    print(f"Saved {len(pushes)} pushes to cache: {file}")

    return pushes
