from datetime import datetime, timedelta
from queuing.hierarchy import *
from common.model import *
from common.utils import random_exit_queue_process_delta
from queuing.tools import *
from pandas import DataFrame

from collections import deque

import random

import logging
logger = logging.getLogger(__name__)

class ChannelsAndDamsQueueSystemOld(QueueSystem):
    @property
    def name(self) -> str:
        return "Channels and Dams System"

    @property
    def description(self) -> str:
        return "A queuing system that prioritizes tasks during a t period then another for a t / 2 period, finite single queues (in and out)."

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.CHANNELS_AND_DAMS

    def _peek(self, queues: dict[PopulationType, deque], population: PopulationType) -> datetime:
        return queues[population][0].time
    
    def _section_duration(self, full_tb, half_tb, pop):
         return full_tb if pop == PopulationType.PREPA else half_tb

    def process(self, inp: Input) -> tuple[DataFrame, DataFrame]:
        # create df with columns population, queue_arrival_time, server_arrival_time, server_exit_time, queue_exit_time
        # in channels and dams, N entry queue, atleast one for ING and one for PREPA, K server, 1 exit queue
        if inp.time_limit is None:
            raise ValueError("Time limit must be specified for Channels and Dams architecture.")
        
        K = inp.num_servers
        servers = deque([datetime.min for _ in range(K)])

        population_queue_sizes = inp.population_queue_sizes

        full_tb = timedelta(seconds=inp.time_limit)
        half_tb = full_tb / 2

        queues = {
            population: deque(maxlen=100)
            for population in population_queue_sizes.keys()
        }

        df = DataFrame(columns=[
            "tag_id",
            "population",
            "exercise_name",
            "queue_arrival_time",
            "server_arrival_time",
            "server_exit_time",
            "queue_exit_time"
        ])

        rejected_df = DataFrame(columns=[
            "tag_id",
            "population",
            "exercise_name",
            "queue_arrival_time",
            "reason"
        ])

        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)
        processed_count = 0
        selected_pop: PopulationType | None = None
        section_start = None
        section_end = None

        for tag in sorted_tags:
            if len(queues[tag.population]) == queues[tag.population].maxlen:
                rejected_df.loc[len(rejected_df)] = { "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "entry_queue_full" }
            else:
                queues[tag.population].append(tag)

            if selected_pop is None:
                if len(queues[PopulationType.PREPA]) > 0:
                    selected_pop = PopulationType.PREPA
                elif len(queues[PopulationType.ING]) > 0:
                    selected_pop = PopulationType.ING

                if selected_pop is not None:
                    tag_time = self._peek(queues, selected_pop)
                    section_start = tag_time
                    section_end = tag_time + self._section_duration(full_tb, half_tb, selected_pop)
                    logger.info("population: %s, section_start: %s, section_end: %s", selected_pop, section_start, section_end)

            if selected_pop is None:
                continue

            if len(queues[selected_pop]) == 0:
                selected_pop = PopulationType.ING if selected_pop == PopulationType.PREPA else PopulationType.PREPA
                if len(queues[selected_pop]) == 0:
                    continue
                tag_time = self._peek(queues, selected_pop)
                section_start = tag_time
                section_end = datetime.max
                logger.info("Processed tags: %s ", processed_count)
                logger.info("population: %s, section_start: %s, section_end: %s", selected_pop, section_start, section_end)
                processed_count = 0

            elif self._peek(queues, selected_pop) >= section_end:
                selected_pop = PopulationType.ING if selected_pop == PopulationType.PREPA else PopulationType.PREPA
                if len(queues[selected_pop]) == 0:
                    continue
                tag_time = self._peek(queues, selected_pop)
                section_start = tag_time
                section_end = tag_time + self._section_duration(full_tb, half_tb, selected_pop)
                logger.info("Processed tags: %s ", processed_count)
                logger.info("population: %s, section_start: %s, section_end: %s", selected_pop, section_start, section_end)
                processed_count = 0

            if len(queues[selected_pop]) == 0:
                continue

            tag = queues[selected_pop].popleft()
            processed_count += 1

            pops = ["prepa"]
            if selected_pop == PopulationType.ING:
                pops = ["ing_strong", "ing_mean"]

            entry_queue_count_at_time = get_queue_occupancy_at_time(df, "queue_arrival_time", "server_arrival_time", {"population": pops}, tag.time)
            exit_queue_count_at_time = get_queue_occupancy_at_time(df, "server_exit_time", "queue_exit_time", {"population": pops}, tag.time)

            if entry_queue_count_at_time >= population_queue_sizes[selected_pop]:
                rejected_df.loc[len(rejected_df)] = { "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "entry_queue_full" }
                continue

            if exit_queue_count_at_time >= population_queue_sizes[selected_pop]:
                rejected_df.loc[len(rejected_df)] = { "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "exit_queue_full" }
                continue
            
            queue_arrival_time = tag.time

            server_available_time = servers.popleft()
            server_arrival_time = max(queue_arrival_time, server_available_time)

            pmin, pmax = inp.registry[tag.exercise_name]
            processing_time = timedelta(milliseconds=random.randint(pmin, pmax))
            server_exit_time = server_arrival_time + processing_time

            queue_exit_time = server_exit_time + random_exit_queue_process_delta()

            servers.append(server_exit_time)

            df = df._append({
                "tag_id": tag.id,
                "population": get_population(tag.population, tag.is_strong),
                "exercise_name": tag.exercise_name,
                "queue_arrival_time": queue_arrival_time,
                "server_arrival_time": server_arrival_time,
                "server_exit_time": server_exit_time,
                "queue_exit_time": queue_exit_time
            }, ignore_index=True)

        logger.info("Processed tags: %s (rejected: %s)", processed_count, len(rejected_df))
        return df, rejected_df
