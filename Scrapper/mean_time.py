import json
import pandas 
import pathlib

FOLDER = pathlib.Path(__file__).parent

def main():
    # get all json files in the current folder, store them in a list as dict
    json_files = list(FOLDER.glob("*.json"))
    data = []
    for json_file in json_files:
        with open(json_file, "r") as f:
            data.append(json.load(f))

    '''
    each dict is a dictionary with units such as 
    "int_vector_max": {
        "tags": {
            "fd5dd866-0eee-4742-8c84-a67a1f994370": {
                "submission_date": "2023-10-04 15:46:00",
                "rank": "A",
                "time": 0,
                "percentile": 1
            }
        }
    },

    where we have an exercise, tag, and the time it took in ms
    '''

    # each dict contains the same exercises (they may not contain all exercises)
    # we want to compute the mean time per exercise across all dicts
    exercise_times = {}
    for entry in data:
        for exercise, exercise_data in entry.items():
            if exercise not in exercise_times:
                exercise_times[exercise] = []
            for tag_id, tag_data in exercise_data["tags"].items():
                if tag_data['time'] == -1:
                    continue
                if tag_data["time"] > 30000:
                    exercise_times[exercise].append(5000)
                    continue
                exercise_times[exercise].append(tag_data["time"])

    mean_times = {}
    for exercise, times in exercise_times.items():
        if exercise == "my_pow":
            print(times)
        if times != []:
            mean_times[exercise] = int(sum(times) / len(times))
    
    # now write mean times in json to mean_times.json
    with open(FOLDER / "mean_times.json", "w") as f:
        json.dump(mean_times, f, indent=4)

if __name__ == "__main__":
    main()
    