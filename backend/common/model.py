import pydantic
from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Union, Optional, Tuple, List
from pydantic import BaseModel
from datetime import timedelta

class PopulationType(str, Enum):
    ING = 'ING'
    PREPA = 'PREPA'

    def __str__(self):
        return self.value

class ArchitectureType(str, Enum):
    WATERFALL = 'WATERFALL'
    CHANNELS_AND_DAMS = 'CHANNELS_AND_DAMS'
    ANTI_PRIORITY = 'ANTI_PRIORITY'
    CALENDAR_PRIORITY = 'CALENDAR_PRIORITY'

    def __str__(self):
        return self.value

class Tag(pydantic.BaseModel):
    id: UUID
    time : datetime
    population: PopulationType
    exercise_name: str
    user_id: UUID
    is_strong: bool

    def __str__(self):
        return f"Tag(id={self.id}, time={self.time}, population={self.population}, exercise_name={self.exercise_name})"


class ExerciseRegistry(BaseModel):
    exercises: dict[str, Tuple[int, int]]

class PopulationCalendarPriority(BaseModel):
    population: PopulationType
    priority_schedules: List[Tuple[Tuple[Tuple[int, int, int], Tuple[int, int, int]], float]]

class CalendarPriorityConfig(BaseModel):
    priorities : dict[PopulationType, list[PopulationCalendarPriority]]

class Input(BaseModel):
    num_servers : int = 1
    architecture: ArchitectureType
    tags: list[Tag]
    registry: ExerciseRegistry
    population_queue_sizes : Optional[dict[PopulationType, int]] = None
    time_limit: Optional[timedelta] = timedelta(seconds=5)
    calendar_priority_config: Optional[CalendarPriorityConfig] = None
