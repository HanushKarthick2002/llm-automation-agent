from fastapi import FastAPI, HTTPException, Query
import subprocess
import os
import requests
import json
import glob
import sqlite3
from datetime import datetime

app = FastAPI()
os.environ['LLMFOUNDRY_TOKEN'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhhbnVzaC52QHN0cmFpdmUuY29tIn0.wO2I5bQROtEor8AeknXT91ieB8Yt-IdpaRf0S8jA9Jk"

LLM_API_URL = "https://llmfoundry.straive.com/openai/v1/chat/completions"
LLM_HEADERS = {"Authorization": f"Bearer {os.environ['LLMFOUNDRY_TOKEN']}:my-test-project"}

def run_subprocess(command):
    try:
        subprocess.run(command, check=True, shell=True)
        return {"status": "success"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))

def call_llm(prompt):
    response = requests.post(LLM_API_URL, headers=LLM_HEADERS, json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    })
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail=response.text)

@app.post("/run")
def run_task(task: str = Query(...)):
    try:
        prompt = f"""Identify which predefined task (A1 to A10) matches this user description: '{task}' and respond with only the task code.Classify the following task into one of these categories:
        A1: generate_data
A2: format_markdown
A3: count_dates
A4: sort_json
A5: process_logs
A6: extract_headers
A7: extract_email
A8: process_image
A9: find_similar
A10: query_database
        """
        llm_response = call_llm(prompt)
        selected_task = llm_response['choices'][0]['message']['content'].strip()

        if selected_task == "A1":
            run_subprocess("pip install uv || true && uv pip install requests && python datagen.py ${user.email}")
        elif selected_task == "A2":
            run_subprocess("npx prettier@3.4.2 --write ./data/format.md")
        elif selected_task == "A3":
            with open('./data/dates.txt') as f:
                wednesdays = sum(1 for line in f if datetime.strptime(line.strip(), '%Y-%m-%d').weekday() == 2)
            with open('./data/dates-wednesdays.txt', 'w') as out:
                out.write(str(wednesdays))
        elif selected_task == "A4":
            with open('./data/contacts.json') as f:
                data = json.load(f)
                contacts = data['contacts'] 
            contacts.sort(key=lambda x: (x['last_name'], x['first_name']))
            with open('./data/contacts-sorted.json', 'w') as out:
                json.dump(contacts, out, indent=4)
        elif selected_task == "A5":
            logs = sorted(glob.glob('*.log'), key=os.path.getctime, reverse=True)[:10]
            with open('./data/logs-recent.txt', 'w') as out:
                for log in logs:
                    with open(log) as f:
                        out.write(f.readline())
        elif selected_task == "A6":
            index = {}
            for md_file in glob.glob('./data/docs/*.md'):
                with open(md_file) as f:
                    for line in f:
                        if line.startswith('# '):
                            index[os.path.basename(md_file)] = line.strip('# ').strip()
                            break
            with open('./data/docs/index.json', 'w') as out:
                json.dump(index, out, indent=4)
        elif selected_task == "A7":
            with open('./data/email.txt') as f:
                email_content = f.read()
            response = call_llm("Extract the sender email from this email: " + email_content)
            sender_email = response['choices'][0]['message']['content']
            with open('./data/email-sender.txt', 'w') as out:
                out.write(sender_email)
        elif selected_task == "A8":
            image_path = './data/a.png'
            response = call_llm(f"Extract the credit card number from the image: {image_path}")
            card_number = response['choices'][0]['message']['content'].replace(' ', '')
            with open('./data/credit-card.txt', 'w') as out:
                out.write(card_number)
        elif selected_task == "A9":
            with open('./data/comments.txt') as f:
                comments = f.readlines()
            similar = comments[:2]
            with open('./data/comments-similar.txt', 'w') as out:
                out.writelines(similar)
        elif selected_task == "A10":
            conn = sqlite3.connect('./data/ticket-sales.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
            total = cursor.fetchone()[0]
            with open('./data/ticket-sales-gold.txt', 'w') as out:
                out.write(str(total))
        else:
            raise HTTPException(status_code=400, detail="Unknown task")

        return {"status": "success", "task": selected_task}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
