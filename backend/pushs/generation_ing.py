import json
import os
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import t
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter, defaultdict
from common.model import *
from uuid import UUID, uuid4

def generate_users(PARAMS):
    n_strong = int(PARAMS["population_size"] * PARAMS["percentage_strong"])
    n_normal = PARAMS["population_size"] - n_strong
    users = [{"id": uuid4(), "is_strong": True} for _ in range(n_strong)]
    users += [{"id": uuid4(), "is_strong": False} for _ in range(n_normal)]
    return users

def pushes_per_person(PARAMS, is_strong, difficulty):
    if is_strong:
        base_mean = PARAMS["gamma_strong"]["base_mean"]
        max_mean = PARAMS["gamma_strong"]["max_mean"]
    else:
        base_mean = PARAMS["gamma_normal"]["base_mean"]
        max_mean = PARAMS["gamma_normal"]["max_mean"]

    mean = base_mean + difficulty * (max_mean - base_mean)
    shape = PARAMS["gamma_shape"]
    scale = mean / shape

    pushes = np.random.gamma(shape, scale)
    return max(1, int(round(pushes)))

def generate_pushes_ing(PARAMS, exo_day_times, diffs):
    PARAMS["nb_points"] = (PARAMS["window_end"] - PARAMS["window_start"]) * PARAMS["nb_points_per_hour"]

    users = generate_users(PARAMS)
    all_pushes = []

    for (exo_id, day), hours in exo_day_times.items():
        if len(hours) < 2:
            continue

        difficulty = diffs[exo_id]

        df, loc, scale = t.fit(hours)
        t_hours = np.linspace(0, PARAMS["window_end"] - PARAMS["window_start"], PARAMS["nb_points"])
        density = t.pdf(t_hours, df=df, loc=loc, scale=scale)
        density[density < 0] = 0
        density /= density.sum()

        day_start_dt = datetime.combine(day, datetime.min.time()) + timedelta(hours=PARAMS["window_start"])

        for user in users:
            n_push = pushes_per_person(PARAMS, user["is_strong"], difficulty)
            push_times = np.random.choice(t_hours, size=n_push, p=density)

            for h in push_times:
                dt = day_start_dt + timedelta(hours=float(h + np.random.normal(0, PARAMS["jitter_hours"])))
                all_pushes.append(Tag(
                    id=uuid4(),
                    time=dt,
                    population=PopulationType.ING,
                    exercise_name=exo_id,
                    user_id=user["id"],
                    is_strong=user["is_strong"]
                ))

    exo = defaultdict(int)
    for p in all_pushes:
        exo[p.exercise_name] += 1

    print("Number of different exos", len(exo))

    return all_pushes
