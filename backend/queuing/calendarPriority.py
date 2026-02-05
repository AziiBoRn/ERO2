from datetime import timedelta
from queuing.hierarchy import *
from common.model import *
from common.utils import *
from pandas import DataFrame
import pandas as pd
import math
import logging

from collections import deque
from queuing.tools import *

import random

def get_priority_for_time(current_time: datetime, priority_schedules: List[Tuple[Tuple[datetime], float]]) -> float:
    day_of_week = current_time.weekday()
    hour = current_time.hour
    minute = current_time.minute
    
    for schedule in priority_schedules:
        (start, end), priority = schedule
        start_day, start_hour, start_min = start
        end_day, end_hour, end_min = end
        
        if start_day == end_day:
            if day_of_week == start_day:
                if (start_hour, start_min) <= (hour, minute) < (end_hour, end_min):
                    return priority
        else:
            if day_of_week == start_day:
                if (hour, minute) >= (start_hour, start_min):
                    return priority
            elif day_of_week == end_day:
                if (hour, minute) < (end_hour, end_min):
                    return priority
    
    return 0.0

class CalendarPriorityQueueSystem(QueueSystem):
    @property
    def name(self) -> str:
        return "Calendar Priority Queue System"

    @property
    def description(self) -> str:
        return "A queuing system that gives priority on certain days to certain populations, finite queues."

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.WATERFALL

    def process(self, inp : Input) -> tuple[DataFrame, DataFrame]:
        if inp.calendar_priority_config is None:
            raise ValueError("Calendar priority config must be provided for Calendar Priority architecture.")
        
        K = inp.num_servers
        servers = deque([datetime.min for _ in range(K)])

        population_queue_sizes = inp.population_queue_sizes
        
        queues = {
            population: deque()
            for population in population_queue_sizes.keys()
        }

        df_list = []
        rejected_df_list = []

        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)
        step = len(sorted_tags) // 10

        entry_occupancies = {
            PopulationType.ING: deque(),
            PopulationType.PREPA: deque()
        }

        exit_occupancies = {
            PopulationType.ING: deque(),
            PopulationType.PREPA: deque()
        }

        for i, tag in enumerate(sorted_tags):
            if (i+1) % step == 0:
                logging.info(f"Processing tag {i+1}/{len(sorted_tags)}")

            queues[tag.population].append(tag)
            current_time = tag.time

            for pop in entry_occupancies.keys():
                while len(entry_occupancies[pop]) > 0 and entry_occupancies[pop][0] <= current_time:
                    entry_occupancies[pop].popleft()
                while len(exit_occupancies[pop]) > 0 and exit_occupancies[pop][0][1] <= current_time:
                    exit_occupancies[pop].popleft()

            populations = list(queues.keys())

            weights = []
            for population in populations:
                queue_size = len(queues[population])
                if queue_size == 0:
                    weights.append(0)
                    continue
                
                population_priorities = inp.calendar_priority_config.priorities.get(population, [])
                priority = 0.0
                for pop_priority in population_priorities:
                    priority = get_priority_for_time(current_time, pop_priority.priority_schedules)
                    if priority > 0:
                        break
                
                weight = priority * queue_size
                weights.append(weight)

            total_weight = sum(weights)
            if total_weight == 0:
                break
            probabilities = [weight / total_weight for weight in weights]

            selected_population = populations[probabilities.index(max(probabilities))] # random.choices(populations, weights=probabilities, k=1)[0]

            tag = queues[selected_population].popleft()
            
            entry_queue_count_at_time = len(entry_occupancies[selected_population])
            exit_queue_count_at_time = sum(
                1 for entry_time, exit_time in exit_occupancies[selected_population]
                if entry_time <= current_time < exit_time
            )

            if entry_queue_count_at_time >= population_queue_sizes[selected_population]:
                rejected_df_list.append({ "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "entry_queue_full" })
                continue

            if exit_queue_count_at_time >= population_queue_sizes[selected_population]:
                rejected_df_list.append({ "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "exit_queue_full" })
                continue

            queue_arrival_time = tag.time

            server_available_time = servers.popleft()
            server_arrival_time = max(queue_arrival_time, server_available_time)

            pmin, pmax = inp.registry.exercises[tag.exercise_name]
            processing_time = random_server_setup_delta() + timedelta(milliseconds=random.randint(pmin, pmax))
            server_exit_time = server_arrival_time + processing_time
            queue_exit_time = server_exit_time + random_exit_queue_process_delta()

            entry_occupancies[selected_population].append(server_arrival_time)
            exit_occupancies[selected_population].append((server_exit_time, queue_exit_time))

            servers.append(server_exit_time)

            df_list.append({
                "tag_id": tag.id,
                "population": get_population(tag.population, tag.is_strong),
                "exercise_name": tag.exercise_name,
                "queue_arrival_time": queue_arrival_time,
                "server_arrival_time": server_arrival_time,
                "server_exit_time": server_exit_time,
                "queue_exit_time": queue_exit_time
            })
        
        return DataFrame(df_list), DataFrame(rejected_df_list)
