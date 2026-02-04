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

class AntiPriorityQueueSystem(QueueSystem):
    @property
    def name(self) -> str:
        return "Anti Priority Queue System"
    
    @property
    def description(self) -> str:
        return "A queuing system that prioritizes tasks with less elements to process, finite single queues (in and out)."
    
    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.ANTI_PRIORITY

    def process(self, inp : Input) -> tuple[DataFrame, DataFrame]:
        # create df with columns population, queue_arrival_time, server_arrival_time, server_exit_time, queue_exit_time
        # in anti-priority, N entry queue, atleast one for ING and one for PREPA, K server, 1 exit queue

        K = inp.num_servers
        servers = deque([datetime.min for _ in range(K)])

        population_queue_sizes = inp.population_queue_sizes
        
        queues = {
            population: deque()
            for population in population_queue_sizes.keys()
        }

        base_weights = {
            population: 1
            for population in population_queue_sizes.keys()
        }

        current_weight = base_weights.copy()

        tags_history = deque(maxlen=100)
        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)

        df_list = []
        rejected_df_list = []

        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)
        step = len(sorted_tags) // 1000

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
            weights = [current_weight[population] if len(queues[population]) > 0 else 0 for population in populations]
            
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

            tags_history.append(tag)
            
            population_counts = {}
            for t in tags_history:
                population_counts[t.population] = population_counts.get(t.population, 0) + 1
            for population in current_weight.keys():
                count_in_history = population_counts.get(population, 0)
                current_weight[population] = max(1, len(tags_history) - count_in_history)
   
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




        