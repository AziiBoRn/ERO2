from datetime import timedelta
from queuing.hierarchy import *
from common.model import *
from common.utils import *
from queuing.tools import *
from pandas import DataFrame

from collections import deque

import random
import time

class WaterfallQueueSystem(QueueSystem):
    @property
    def name(self) -> str:
        return "Waterfall Queue System"

    @property
    def description(self) -> str:
        return "A queuing system that processes tasks in a sequential manner, infinite single queues (in and out)."

    @property
    def architecture_type(self) -> ArchitectureType:
        return ArchitectureType.WATERFALL

    def process(self, inp : Input) -> tuple[DataFrame, DataFrame]:
        # in waterfall, only one entry queue, K server, one exit queue
        # queues are infinite, so no rejections

        K = inp.num_servers
        servers = deque([datetime.min for _ in range(K)])

        sorted_tags = sorted(inp.tags, key=lambda tag: tag.time)
        df_list = []

        for i, tag in enumerate(sorted_tags):
            step = len(sorted_tags) // 1000

            if step > 0 and i % step == 0:
                print(f"Processing tag {i}/{len(inp.tags)}")

            queue_arrival_time = tag.time

            server_available_time = servers.popleft()
            server_arrival_time = max(queue_arrival_time, server_available_time)

            pmin, pmax = inp.registry.exercises[tag.exercise_name]
            processing_time = random_server_setup_delta() + timedelta(milliseconds=random.randint(pmin, pmax))
            server_exit_time = server_arrival_time + processing_time

            queue_exit_time = server_exit_time

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

        return DataFrame(df_list), DataFrame()
