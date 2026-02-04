import json
from pathlib import Path
from math import isfinite

INPUT_DIR = "results"

SCENARIO_MAPPING = {
    "CalendarPriority_Base": ("Calendar Priority", "Cas de base"),
    "CalendarPriority_50Servers": ("Calendar Priority", "50 serveurs"),
    "CalendarPriority_70Strong": ("Calendar Priority", "70\\% d'élèves fort"),
    "CalendarPriority_1500ING_300PREPA": ("Calendar Priority", "1500 ING - 300 PREPA"),

    "ChannelsAndDams_5s": ("T5s", "Cas de base"),
    "ChannelsAndDams_5s_50Servers": ("T5s", "50 serveurs"),
    "ChannelsAndDams_5s_70Strong": ("T5s", "70\\% d'élèves fort"),
    "ChannelsAndDams_5s_1500ING_300PREPA": ("T5s", "1500 ING - 300 PREPA"),

    "ChannelsAndDams_30S": ("T30s", "Cas de base"),
    "ChannelsAndDams_30s_50Servers": ("T30s", "50 serveurs"),
    "ChannelsAndDams_30s_70Strong": ("T30s", "70\\% d'élèves fort"),
    "ChannelsAndDams_30s_1500ING_300PREPA": ("T30s", "1500 ING - 300 PREPA"),

    "AntiPriority_Base_H100": ("H100", "Cas de base"),
    "AntiPriority_50Servers_H100": ("H100", "50 serveurs"),
    "AntiPriority_H100_70Strong": ("H100", "70\\% d'élèves fort"),
    "AntiPriority_H100_1500ING_600PREPA": ("H100", "1500 ING - 600 PREPA"),

    "AntiPriority_Base_H10": ("H10", "Cas de base"),
    "AntiPriority_50Servers_H10": ("H10", "50 serveurs"),
    "AntiPriority_H10_70Strong": ("H10", "70\\% d'élèves fort"),
    "AntiPriority_H10_1500ING_600PREPA": ("H10", "1500 ING - 600 PREPA"),

    "Waterfall_Base": ("Waterfall", "Cas de base"),
    "Waterfall_50_Servers": ("Waterfall", "50 serveurs"),
    "Waterfall_70_Strong": ("Waterfall", "70\\% d'élèves fort"),
    "Waterfall_ING1500_PREPA300": ("Waterfall", "1500 ING - 300 PREPA"),
}

POPULATIONS = ["prepa", "ing_mean", "ing_strong"]
NUM_COLS = ["mean", "max", "P50", "P90", "occupancy"]

def load_population_stats(pop):
    data = {}
    for d in Path(INPUT_DIR).iterdir():
        if not d.is_dir() or d.name not in SCENARIO_MAPPING:
            continue
        json_path = d / "stats.json"
        if not json_path.exists():
            continue
        with open(json_path) as f:
            content = json.load(f)
        data[d.name] = content.get(pop)
    return data

def compute_mins(data):
    mins = {k: None for k in NUM_COLS}
    for stats in data.values():
        if not stats:
            continue
        wt = stats["waiting_time"]
        vals = {
            "mean": wt["mean"],
            "max": wt["max"],
            "P50": wt["P50"],
            "P90": wt["P90"],
            "occupancy": stats["avg_queue_occupancy"],
        }
        for k, v in vals.items():
            if isinstance(v, (int, float)) and isfinite(v):
                mins[k] = v if mins[k] is None else min(mins[k], v)
    return mins

def fmt(val, is_best, perc=False):
    if val is None or val == "-":
        return "-"
    if perc:
        val_str = f"{val:.2f}\\%"
    else:
        val_str = f"{val:.2f}"
    return f"\\textbf{{{val_str}}}" if is_best else val_str

def format_row(stats, mins):
    if not stats:
        return "& & & & & & \\\\"
    wt = stats["waiting_time"]
    return (
        f"{fmt(stats['percent_rejected'], stats['percent_rejected']==mins.get('percent_rejected', None), perc=True)} & "
        f"{fmt(wt['mean'], wt['mean'] == mins['mean'])} & "
        f"{fmt(wt['max'], wt['max'] == mins['max'])} & "
        f"{fmt(wt['P50'], wt['P50'] == mins['P50'])} & "
        f"{fmt(wt['P90'], wt['P90'] == mins['P90'])} & "
        f"{fmt(stats['avg_queue_occupancy'], stats['avg_queue_occupancy'] == mins['occupancy'])} \\\\"
    )

def generate_combined_table(output_file="results/table_all_pop.tex"):
    pop_to_name = {
        "prepa": "Prepa",
        "ing_mean": "ING Normal",
        "ing_strong": "ING Fort"
    }

    with open(output_file, "w") as f:
        for pop in POPULATIONS:
            data = load_population_stats(pop)
            mins = compute_mins(data)
            f.write(f"\n\\subsubsection{{{pop_to_name[pop]}}}\n\n")
            f.write("""\\begin{table}[H]
\\footnotesize
\\centering
\\renewcommand{\\arraystretch}{1.5}
\\setlength{\\tabcolsep}{5pt}
\\begin{tabular}{|p{1cm}|p{3cm}|c|c|c|c|c|c|}
\\hline
\\multicolumn{2}{|c|}{\\textbf{Scénario}} & \\textbf{\\% Tags rejetés} & \\multicolumn{4}{c|}{\\textbf{Temps d'attente}} & \\textbf{Occupation moy.} \\\\
\\hline
\\multicolumn{2}{|l|}{\\cellcolor{gray!30}\\hspace{0.5em}} & \\cellcolor{gray!30} & \\textbf{Mean} & \\textbf{Max} & \\textbf{P50} & \\textbf{P90} & \\cellcolor{gray!30} \\\\
\\hline
""")
            # Calendar Priority
            f.write("\\rowcolor{gray!30}\\multicolumn{2}{|c|}{Calendar Priority} & & & & & & \\\\\n")
            for k in ["CalendarPriority_Base","CalendarPriority_50Servers","CalendarPriority_70Strong","CalendarPriority_1500ING_300PREPA"]:
                f.write(f"\\multicolumn{{2}}{{|l|}}{{{SCENARIO_MAPPING[k][1]}}} & {format_row(data.get(k), mins)}\n")
            f.write("\\hline\n")

            # Channels & Dams
            f.write("\\rowcolor{gray!30}\\multicolumn{2}{|c|}{Channels Dams} & & & & & & \\\\\n\\hline\n")
            for label, keys in {"T5s":["ChannelsAndDams_5s","ChannelsAndDams_5s_50Servers","ChannelsAndDams_5s_70Strong","ChannelsAndDams_5s_1500ING_300PREPA"],
                                "T30s":["ChannelsAndDams_30S","ChannelsAndDams_30s_50Servers","ChannelsAndDams_30s_70Strong","ChannelsAndDams_30s_1500ING_300PREPA"]}.items():
                f.write(f"\\multirow{{4}}{{*}}{{{label}}} & {SCENARIO_MAPPING[keys[0]][1]} & {format_row(data.get(keys[0]), mins)}\n")
                for k in keys[1:]:
                    f.write(f"& {SCENARIO_MAPPING[k][1]} & {format_row(data.get(k), mins)}\n")
                f.write("\\hline\n")

            # Anti Priority
            f.write("\\rowcolor{gray!30}\\multicolumn{2}{|c|}{Anti Priority} & & & & & & \\\\\n\\hline\n")
            for label, keys in {"H100":["AntiPriority_Base_H100","AntiPriority_50Servers_H100","AntiPriority_H100_70Strong","AntiPriority_H100_1500ING_600PREPA"],
                                "H10":["AntiPriority_Base_H10","AntiPriority_50Servers_H10","AntiPriority_H10_70Strong","AntiPriority_H10_1500ING_600PREPA"]}.items():
                f.write(f"\\multirow{{4}}{{*}}{{{label}}} & {SCENARIO_MAPPING[keys[0]][1]} & {format_row(data.get(keys[0]), mins)}\n")
                for k in keys[1:]:
                    f.write(f"& {SCENARIO_MAPPING[k][1]} & {format_row(data.get(k), mins)}\n")
                f.write("\\hline\n")

            # Waterfall
            f.write("\\rowcolor{gray!30}\\multicolumn{2}{|c|}{Waterfall} & & & & & & \\\\\n")
            for k in ["Waterfall_Base","Waterfall_50_Servers","Waterfall_70_Strong","Waterfall_ING1500_PREPA300"]:
                f.write(f"\\multicolumn{{2}}{{|l|}}{{{SCENARIO_MAPPING[k][1]}}} & {format_row(data.get(k), mins)}\n")
            f.write("\\hline\n")

            f.write("\\end{tabular}\n\\vspace{1em}\n\\end{table}\n")
    print(f"Generated {output_file}")

if __name__ == "__main__":
    generate_combined_table()
