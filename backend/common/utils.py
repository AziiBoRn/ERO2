import logging
import warnings
import os
import random
from datetime import timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
)

warnings.filterwarnings(
    "ignore",
    message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated",
    category=FutureWarning,
)
EXIT_QUEUE_PROCESS_TIME_MIN = int(os.getenv("EXIT_QUEUE_PROCESS_TIME_MIN", "30"))
EXIT_QUEUE_PROCESS_TIME_MAX = int(os.getenv("EXIT_QUEUE_PROCESS_TIME_MAX", "50"))

def random_exit_queue_process_delta() -> int:
    return timedelta(milliseconds=random.randint(EXIT_QUEUE_PROCESS_TIME_MIN, EXIT_QUEUE_PROCESS_TIME_MAX))

def random_server_setup_delta():
    return timedelta(seconds=random.randint(20, 30))
