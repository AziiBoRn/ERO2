import re
import requests
import uuid
import json
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import time
import random

TOKEN = ''

with open('token.txt', 'r') as file:
    TOKEN = file.read().strip()

API_URLS = {
    'exercise': 'https://intra.forge.epita.fr/epita-ing-assistants-acu/piscine-2026/root/exercises/exercises-c/{EXERCISE_NAME}/{EXERCISE_NAME}',
    'tag': '/epita-ing-assistants-acu/piscine-2026/root/exercises/exercises-c/{EXERCISE_NAME}/{EXERCISE_NAME}/',
    'metrics': 'https://srvc-stats.api.forge.epita.fr/metrics/execution/{TAG_UUID}',
}

EXERCISES_LIST = []

with open('exercises.txt', 'r') as file:
    content = file.read()
    EXERCISES_LIST = content.splitlines()

print(EXERCISES_LIST)

EXTRACTED_DATA = {}
data_lock = threading.Lock()

def tag_thread(exercise, id, counter=0):
    metrics_url = API_URLS['metrics'].format(TAG_UUID=id)
    print(metrics_url)
    metrics_response = requests.get(metrics_url)
    metrics_code = metrics_response.status_code

    print(metrics_code)

    if metrics_code != 200:
        if counter == 100:
            return
        time.sleep(random.randint(10, 40))
        tag_thread(exercise, id, counter + 1)
        return

    with data_lock:
        data = metrics_response.json()
        for key, value in data.items():
            EXTRACTED_DATA[exercise]['tags'][id][key] = value

THREADS = []

for i, exercise in enumerate(EXERCISES_LIST):
    time.sleep(1)
    
    print(f'Processing exercise {i+1}/{len(EXERCISES_LIST)}: {exercise}')
    url = API_URLS['exercise'].format(EXERCISE_NAME=exercise)
    headers = {
        'Cookie': 'role=MANAGER;' + TOKEN
    }
    response = requests.get(url, headers=headers)
    code = response.status_code

    if code != 200:
        print(f'Token has expired, redo the whole process!')
        continue

    text = response.text
    soup = BeautifulSoup(text, 'html.parser')

    uuid_regex = re.compile(
        r".*[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}$"
    )

    EXTRACTED_DATA[exercise] = { 'tags': {} }

    elements = soup.find_all(href=uuid_regex)

    TAGS_IDS = []

    for el in elements:
        href = el["href"]
        uuid = href.split("/")[-1]

        sub = el.select_one(".list__item__subname")
        if sub:
            text = sub.get_text(strip=True)
            raw_date = text.replace("Submitted on ", "")
            dt = datetime.strptime(raw_date, "%B %d, %Y - %H:%M")
        else:
            dt = None

        TAGS_IDS.append(uuid)
        EXTRACTED_DATA[exercise]['tags'][uuid] = { 'submission_date': dt }

    for id in TAGS_IDS:
        thread = threading.Thread(target=tag_thread, args=(exercise, id))
        thread.start()
        THREADS.append(thread)

    print(f'Finished processing exercise {exercise}')


for thread in THREADS:
    thread.join()

with open('result.json', 'w') as outfile:
    json.dump(EXTRACTED_DATA, outfile, default=str, indent=4)