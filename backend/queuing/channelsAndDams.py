from datetime import datetime, timedelta
from queuing.hierarchy import *
from common.model import *
from common.utils import random_exit_queue_process_delta, random_server_setup_delta
from queuing.tools import *
from pandas import DataFrame

from collections import deque

import random

import logging
logger = logging.getLogger(__name__)

class ChannelsAndDamsQueueSystem(QueueSystem):
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
        if inp.time_limit is None:
            raise ValueError("Time limit must be specified for Channels and Dams architecture.")

        K = inp.num_servers
        servers = deque([datetime.min for _ in range(K)])

        population_queue_sizes = inp.population_queue_sizes

        full_tb = inp.time_limit
        half_tb = full_tb / 2

        queues = {
            population: deque()
            for population in population_queue_sizes.keys()
        }

        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)

        selected_pop: PopulationType | None = None
        section_end = datetime.min

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
            time_now = tag.time

            for pop in entry_occupancies.keys():
                while len(entry_occupancies[pop]) > 0 and entry_occupancies[pop][0] <= time_now:
                    entry_occupancies[pop].popleft()
                while len(exit_occupancies[pop]) > 0 and exit_occupancies[pop][0][1] <= time_now:
                    exit_occupancies[pop].popleft()
            
            if selected_pop is None:
                if len(queues[PopulationType.PREPA]) > 0:
                     selected_pop = PopulationType.PREPA
                elif len(queues[PopulationType.ING]) > 0:
                     selected_pop = PopulationType.ING
                
                tag_time = self._peek(queues, selected_pop)
                section_end = tag_time + self._section_duration(full_tb, half_tb, selected_pop)
        
            queue_empty = len(queues[selected_pop]) == 0
            time_expired = False

            if not queue_empty:
                current_head_time = self._peek(queues, selected_pop)
                time_expired = current_head_time >= section_end

            if time_expired or queue_empty:
                other_pop = PopulationType.ING if selected_pop == PopulationType.PREPA else PopulationType.PREPA
                
                if len(queues[other_pop]) > 0:
                    selected_pop = other_pop
                    tag_time = self._peek(queues, selected_pop)
                    section_end = tag_time + self._section_duration(full_tb, half_tb, selected_pop)
                elif queue_empty:
                    selected_pop = None
                    continue
                else:
                    tag_time = self._peek(queues, selected_pop)
                    section_end = tag_time + self._section_duration(full_tb, half_tb, selected_pop)

            if selected_pop is None or len(queues[selected_pop]) == 0:
                continue

            tag = queues[selected_pop].popleft()
            current_time = tag.time

            entry_queue_count_at_time = len(entry_occupancies[selected_pop])
            exit_queue_count_at_time = sum(
                1 for entry_time, exit_time in exit_occupancies[selected_pop]
                if entry_time <= current_time < exit_time
            )

            if entry_queue_count_at_time >= population_queue_sizes[selected_pop]:
                rejected_df_list.append({ "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "entry_queue_full" })
                continue

            if exit_queue_count_at_time >= population_queue_sizes[selected_pop]:
                rejected_df_list.append({ "tag_id": tag.id, "population": get_population(tag.population, tag.is_strong), "exercise_name": tag.exercise_name, "queue_arrival_time": tag.time, "reason": "exit_queue_full" })
                continue
            
            queue_arrival_time = tag.time

            server_available_time = servers.popleft()
            server_arrival_time = max(queue_arrival_time, server_available_time)

            pmin, pmax = inp.registry.exercises[tag.exercise_name]
            processing_time = random_server_setup_delta() + timedelta(milliseconds=random.randint(pmin, pmax))
            server_exit_time = server_arrival_time + processing_time

            queue_exit_time = server_exit_time + random_exit_queue_process_delta()

            entry_occupancies[selected_pop].append(server_arrival_time)
            exit_occupancies[selected_pop].append((server_exit_time, queue_exit_time))

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
