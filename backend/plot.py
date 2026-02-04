from matplotlib import pyplot as plt
import pandas as pd
import json

def get_population_types():
    return ["prepa", "ing_strong", "ing_mean"]

def plot_queue_by_population_type(occupancy_df, rejected_tags_df, name : str):
    fig, ax1 = plt.subplots(figsize=(20, 6))
    
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Queue occupancy', color='tab:blue')
    for pop_type in get_population_types():
        pop_df = occupancy_df[occupancy_df['population'] == pop_type]
        ax1.plot(pop_df['time'], pop_df['queue_occupancy'], marker=None, label=f'{pop_type} (Queue)', linestyle='-')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Number of rejected tags', color='tab:red')
    
    time_min = occupancy_df['time'].min()
    time_max = occupancy_df['time'].max()

    population_types = get_population_types()
    
    for pop_type in population_types:
        pop_rejected = rejected_tags_df[rejected_tags_df['population'] == pop_type]
        if not pop_rejected.empty:
            times = [time_min] + list(pop_rejected['time']) + [time_max]
            counts = [0] + list(pop_rejected['rejected_count']) + [0]
            color = 'tab:red' if pop_type == list(population_types)[0] else 'tab:purple'
            ax2.plot(times, counts, marker=None, label=f'{pop_type} (Rejected)', linestyle='--', alpha=0.7, color=color)
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
    
    plt.title('Queue occupancy and rejected tags by population type over time')
    plt.tight_layout()
    plt.savefig(name)

def plot_waiting_time_by_population_type(waiting_stats_df, name):
    population_types = get_population_types()
    n_pop = len(population_types)
    
    fig, axes = plt.subplots(n_pop, 1, figsize=(20, 4*n_pop), sharex=True)
    
    if n_pop == 1:
        axes = [axes]

    for ax, pop_type in zip(axes, population_types):
        pop_df = waiting_stats_df[waiting_stats_df['population'] == pop_type]

        ax.plot(
            pop_df['time'],
            pop_df['median'],
            linestyle='-',
            label='Median'
        )
        ax.plot(
            pop_df['time'],
            pop_df['p90'],
            linestyle='--',
            label='P90'
        )

        ax.set_title(f'Population: {pop_type}')
        ax.set_ylabel('Waiting time (min)')
        ax.grid(True, alpha=0.3)
        ax.legend()

    axes[-1].set_xlabel('Time')
    plt.tight_layout()
    plt.savefig(name)

def compute_population_stats(
    df_tags: pd.DataFrame,
    rejected_df: pd.DataFrame,
    occupancy_df: pd.DataFrame,
    output_file: str,
    percentiles=[0.5, 0.9]
):
    df_tags = df_tags.copy()
    rejected_df = rejected_df.copy()
    occupancy_df = occupancy_df.copy()

    df_tags['arrival_hour'] = df_tags['queue_arrival_time'].dt.hour

    summary = {}

    populations = df_tags['population'].unique()

    for pop in populations:
        pop_tags = df_tags[df_tags['population'] == pop]

        # Temps d'attente en minutes
        pop_tags['waiting_time_min'] = (
            pop_tags['server_arrival_time'] - pop_tags['queue_arrival_time']
        ).dt.total_seconds() / 60

        mean_wait = pop_tags['waiting_time_min'].mean()
        max_wait = pop_tags['waiting_time_min'].max()
        p_values = pop_tags['waiting_time_min'].quantile(percentiles)
        P50_wait = p_values.get(0.5, None)
        P90_wait = p_values.get(0.9, None)

        if rejected_df.empty:
            percent_rejected = "-"  # met un "-" si le DataFrame est vide
        else:
            pop_rejected = rejected_df[
                (rejected_df['population'] == pop) &
                (rejected_df['reason'] == 'entry_queue_full')
            ]
            percent_rejected = 100 * len(pop_rejected) / len(pop_tags) if len(pop_tags) > 0 else "-"

        # Occupation moyenne de la queue d'entrée
        pop_occ = occupancy_df[occupancy_df['population'] == pop]
        avg_occupancy = pop_occ['queue_occupancy'].mean() if not pop_occ.empty else 0

        summary[pop] = {
            'total_arrivals': len(pop_tags),
            'percent_rejected': percent_rejected,
            'waiting_time': {
                'mean': mean_wait,
                'max': max_wait,
                'P50': P50_wait,
                'P90': P90_wait
            },
            'avg_queue_occupancy': avg_occupancy
        }

    # Écriture JSON
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=4)

    print(f"Population stats written to {output_file}")
    return summary
