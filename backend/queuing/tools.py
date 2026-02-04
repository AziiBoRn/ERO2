from typing import List
import pandas as pd
from datetime import timedelta
from common.model import PopulationType
from functools import reduce
import operator
import numpy as np

def get_population(population: PopulationType, is_strong: bool) -> str:
    if population == PopulationType.PREPA:
        return "prepa"

    strong = "strong" if is_strong else "mean"

    return "ing_" + strong

def get_population_types():
    return ["prepa", "ing_strong", "ing_mean"]

def create_occupancy_by_population_dataframe(df: pd.DataFrame, start_column : str = "queue_arrival_time", end_column : str = "server_arrival_time") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["time", "population", "queue_occupancy"])
    
    start_time = df[start_column].min()
    end_time = df[end_column].max()

    print(f"Calculating occupancy from {start_time} to {end_time}")

    time_range = pd.date_range(start=start_time, end=end_time, freq='10T')
    
    occupancy_results = []
    population_types = get_population_types()
    
    for pop_type in population_types:
        pop_df = df[df['population'] == pop_type].copy()
        
        if pop_df.empty:
            for t in time_range:
                occupancy_results.append({
                    "time": t,
                    "population": pop_type,
                    "queue_occupancy": 0
                })
            continue
        
        starts = pop_df[[start_column]].copy()
        starts['delta'] = 1
        starts = starts.rename(columns={start_column: 'event_time'})
        
        ends = pop_df[[end_column]].copy()
        ends['delta'] = -1
        ends = ends.rename(columns={end_column: 'event_time'})
        
        events = pd.concat([starts, ends], ignore_index=True)
        events = events.sort_values('event_time')
        
        events['occupancy'] = events['delta'].cumsum()
        
        # Using merge_asof for efficient lookup
        query_df = pd.DataFrame({'time': time_range})
        result = pd.merge_asof(
            query_df,
            events[['event_time', 'occupancy']],
            left_on='time',
            right_on='event_time',
            direction='backward'
        )
        
        result['occupancy'] = result['occupancy'].fillna(0).astype(int)
        result['population'] = pop_type
        
        for _, row in result.iterrows():
            occupancy_results.append({
                "time": row['time'],
                "population": pop_type,
                "queue_occupancy": row['occupancy']
            })
    
    return pd.DataFrame(occupancy_results)

def create_rejected_tags_dataframe(rejected_df: pd.DataFrame, reason : str = "entry_queue_full") -> pd.DataFrame:
    if rejected_df.empty:
        return pd.DataFrame(columns=['time', 'population', 'rejected_count'])
        
    rejected_tags_df = rejected_df[['queue_arrival_time', 'population', 'reason']].copy()
    rejected_tags_df = rejected_tags_df[rejected_tags_df['reason'] == reason]
    rejected_tags_df = rejected_tags_df.rename(columns={'queue_arrival_time': 'time'})
    rejected_tags_df['rejected_count'] = 1
    
    rejected_tags_df['time'] = rejected_tags_df['time'].dt.floor('10T')
    
    rejected_tags_df = rejected_tags_df.groupby(['time', 'population'], as_index=False)['rejected_count'].sum()
    rejected_tags_df = rejected_tags_df.sort_values('time')
        
    return rejected_tags_df

def get_queue_occupancy_at_time(
    df: pd.DataFrame,
    start_column: str,
    end_column: str,
    filter: dict[str, str | list[str]],
    query_time
) -> int:
    if filter:
        masks = []
        for k, v in filter.items():
            if isinstance(v, list):
                masks.append(df[k].isin(v))
            else:
                masks.append(df[k] == v)

        filter_mask = reduce(operator.and_, masks)
    else:
        filter_mask = np.ones(len(df), dtype=bool)

    time_mask = (df[start_column] <= query_time) & (df[end_column] > query_time)
    final_mask = filter_mask & time_mask

    return final_mask.sum(), final_mask

def create_waiting_time_stats_dataframe(
    df: pd.DataFrame,
    freq: str = "10T",
    p: float = 0.9
) -> pd.DataFrame:
    df = df.copy()

    df['waiting_time_min'] = (
        df['server_arrival_time'] - df['queue_arrival_time']
    ).dt.total_seconds() / 60

    df['time'] = df['queue_arrival_time'].dt.floor(freq)

    stats_df = (
        df
        .groupby(['time', 'population'])
        ['waiting_time_min']
        .agg(
            median='median',
            p90=lambda x: x.quantile(p)
        )
        .reset_index()
    )

    return stats_df
