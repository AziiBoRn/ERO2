Easy to use.

First you need to grab your TOKEN, go to 
- Open a browser tab
- Press F12
- Then go to 'https://intra.forge.epita.fr/epita-ing-assistants-acu/piscine-2026/root/exercises/exercises-c/'
- then in the 'network' tab of F12, filter by Fetch/XHR and click on 'activities'
- Stay in 'Headers' and copy the whole 'q_session=...' in Cookie (dont take the 'role=MANAGER;')
- Paste that full token in a new file 'token.txt' in this folder

Then run `python main.py`, wait till it finishes (30s - 1m), a file 'result.json' will be created.

Rename it 'result_login.txt', and push it, you're all set!!