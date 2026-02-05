import pandas as pd
import random
import json
import pathlib
import os

import common.utils

from common.model import *
from common.model import PopulationType
from datetime import datetime, timedelta
from plot import *

from queuing.antiPriorityQueue import AntiPriorityQueueSystem
from queuing.waterfall import WaterfallQueueSystem
from queuing.channelsAndDams import ChannelsAndDamsQueueSystem
from queuing.calendarPriority import CalendarPriorityQueueSystem
from queuing.tools import *

from pushs.generation import generate_pushes_cached

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

SCENARIO_NAME = "Test"

FOLDER = pathlib.Path(__file__).parent
MEAN_TIMES = json.load(open(FOLDER /"mean_times.exe"))

QUEUE_SYSTEMS = {
    ArchitectureType.WATERFALL: WaterfallQueueSystem(),
    ArchitectureType.ANTI_PRIORITY: AntiPriorityQueueSystem(),
    ArchitectureType.CHANNELS_AND_DAMS: ChannelsAndDamsQueueSystem(),
    ArchitectureType.CALENDAR_PRIORITY: CalendarPriorityQueueSystem(),
}

def main(inp : Input):
    path = "results/" + SCENARIO_NAME + "/"
    os.makedirs(path, exist_ok=True)

    queue_system = QUEUE_SYSTEMS.get(inp.architecture)
    df, rejected_df = queue_system.process(inp)

    entry_occupancy_df = create_occupancy_by_population_dataframe(df)
    exit_occupancy_df = create_occupancy_by_population_dataframe(df, start_column="server_exit_time", end_column="queue_exit_time")
    entry_rejected_tags_df = create_rejected_tags_dataframe(rejected_df, reason="entry_queue_full")
    exit_rejected_tags_df = create_rejected_tags_dataframe(rejected_df, reason="exit_queue_full")
    waiting_df = create_waiting_time_stats_dataframe(df)

    plot_queue_by_population_type(entry_occupancy_df, entry_rejected_tags_df, name=path + "entry_queue.png")
    plot_queue_by_population_type(exit_occupancy_df, exit_rejected_tags_df, name=path + "exit_queue.png")
    plot_waiting_time_by_population_type(waiting_df, name=path + "waiting_time.png")

    stats_json_file = path + "stats.json"
    population_stats = compute_population_stats(
        df_tags=df,
        rejected_df=rejected_df,
        occupancy_df=entry_occupancy_df,
        output_file=stats_json_file
    )

    #print(population_stats)

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    tags = generate_pushes_cached(invalidate = False)

    registry = ExerciseRegistry(exercises={
        'Exo1': (5000, 10000),
    })

    for exercise, time in MEAN_TIMES.items():
        registry.exercises[exercise] = (time, time)
    
    ing_priority = PopulationCalendarPriority(
        population=PopulationType.ING,
        priority_schedules=[
            # Monday to Thursday: 2pm (14:00) to midnight (00:00) - priority 0.9
            (((0, 14, 0), (1, 0, 0)), 0.9),  # Monday 2pm to Tuesday midnight
            (((1, 14, 0), (2, 0, 0)), 0.9),  # Tuesday 2pm to Wednesday midnight
            (((2, 14, 0), (3, 0, 0)), 0.9),  # Wednesday 2pm to Thursday midnight
            (((3, 14, 0), (4, 0, 0)), 0.9),  # Thursday 2pm to Friday midnight
            
            # Monday to Thursday: midnight (00:00) to 2pm (14:00) - priority 0.1
            (((0, 0, 0), (0, 14, 0)), 0.1),  # Monday midnight to 2pm
            (((1, 0, 0), (1, 14, 0)), 0.1),  # Tuesday midnight to 2pm
            (((2, 0, 0), (2, 14, 0)), 0.1),  # Wednesday midnight to 2pm
            (((3, 0, 0), (3, 14, 0)), 0.1),  # Thursday midnight to 2pm
            
            # Friday to Sunday: all day - priority 0.4
            (((4, 0, 0), (5, 0, 0)), 0.4),  # Friday all day
            (((5, 0, 0), (6, 0, 0)), 0.4),  # Saturday all day
            (((6, 0, 0), (7, 0, 0)), 0.4),  # Sunday all day (wraps to next Monday)
        ]
    )
    
    prepa_priority = PopulationCalendarPriority(
        population=PopulationType.PREPA,
        priority_schedules=[
            # Monday to Thursday: midnight (00:00) to 2pm (14:00) - priority 0.9
            (((0, 0, 0), (0, 14, 0)), 0.9),  # Monday midnight to 2pm
            (((1, 0, 0), (1, 14, 0)), 0.9),  # Tuesday midnight to 2pm
            (((2, 0, 0), (2, 14, 0)), 0.9),  # Wednesday midnight to 2pm
            (((3, 0, 0), (3, 14, 0)), 0.9),  # Thursday midnight to 2pm
            
            # Monday to Thursday: 2pm (14:00) to midnight (00:00) - priority 0.1
            (((0, 14, 0), (1, 0, 0)), 0.1),  # Monday 2pm to Tuesday midnight
            (((1, 14, 0), (2, 0, 0)), 0.1),  # Tuesday 2pm to Wednesday midnight
            (((2, 14, 0), (3, 0, 0)), 0.1),  # Wednesday 2pm to Thursday midnight
            (((3, 14, 0), (4, 0, 0)), 0.1),  # Thursday 2pm to Friday midnight
            
            # Friday to Sunday: all day - priority 0.6
            (((4, 0, 0), (5, 0, 0)), 0.6),  # Friday all day
            (((5, 0, 0), (6, 0, 0)), 0.6),  # Saturday all day
            (((6, 0, 0), (7, 0, 0)), 0.6),  # Sunday all day (wraps to next Monday)
        ]
    )
    
    calendar_config = CalendarPriorityConfig(
        priorities={
            PopulationType.ING: [ing_priority],
            PopulationType.PREPA: [prepa_priority]
        }
    )
    
    main(Input(tags=tags, architecture=ArchitectureType.CALENDAR_PRIORITY, registry=registry, num_servers=200, population_queue_sizes={PopulationType.ING: 3000, PopulationType.PREPA: 600}, calendar_priority_config=calendar_config))
