import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from uuid import uuid4
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import t
from common.model import *
from uuid import UUID, uuid4

def generate_pushes_prepa(PARAMS):
    start_date = PARAMS.get("start_date", datetime.today()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    users = [uuid4() for _ in range(PARAMS["population_size"])]
    all_pushes = []

    total_days = PARAMS["nb_weeks"] * 7
    resolution = PARAMS["time_resolution_min"] / 60

    total_pushes = int(PARAMS["population_size"] * PARAMS["mean_pushes_per_student"] *
                       sum(PARAMS["week_weights"].values()) * PARAMS["nb_weeks"] * 3)

    hours_grid = np.arange(0, total_days*24 + 2, resolution)
    density_grid = np.zeros_like(hours_grid)

    for day_idx in range(total_days):
        day_type = "weekend" if (day_idx % 7) >= 5 else "weekday"
        params_day = PARAMS["daily_distributions"][day_type]
        peak_hour = params_day["t_student"]["peak_hour"]
        df = params_day["t_student"]["df"]
        scale = params_day["t_student"]["scale"]
        weight_exp = params_day["exponential"]["weight"]
        exp_scale = params_day["exponential"]["scale"]

        day_weight = PARAMS["week_weights"][day_idx % 7]

        start = day_idx * 24
        end = (day_idx + 1) * 24 + 2
        mask = (hours_grid >= start) & (hours_grid < end)
        hours_in_day = hours_grid[mask] - start

        density_t = t.pdf(hours_in_day, df=df, loc=peak_hour, scale=scale)
        density_exp = np.exp(-(hours_in_day - peak_hour) / exp_scale)
        density_exp[hours_in_day < peak_hour] = 0

        density_day = (1 - weight_exp) * density_t + weight_exp * density_exp
        density_day[density_day < 0] = 0

        density_day *= day_weight
        density_grid[mask] += density_day

    density_grid /= density_grid.sum()

    push_hours = np.random.choice(hours_grid, size=total_pushes, p=density_grid)

    for h in push_hours:
        day_offset = int(h // 24)
        hour_in_day = h % 24
        dt = start_date + timedelta(days=day_offset, hours=hour_in_day)
        uid = np.random.choice(users)

        all_pushes.append(Tag(
            id=uuid4(),
            time=dt,
            population=PopulationType.PREPA,
            exercise_name="Exo1",
            user_id=uid,
            is_strong=False
        ))

    return all_pushes
