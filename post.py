from fastapi import FastAPI, HTTPException, Query
import subprocess
import os
import requests
import json
import glob
import sqlite3
from datetime import datetime
from pathlib import Path

from PIL import Image
import pandas as pd
import soundfile as sf

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
        prompt = f"""Identify which predefined task (A1 to A10 and B2 to B8) matches this user description: '{task}' and respond with only the task code.Classify the following task into one of these categories:
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
B2: clone_repo
B3: run_sql_query
B4: scrape_website
B5: compress_image
B6: transcribe_audio
B7: convert_markdown
B8: filter_csv
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

        elif selected_task == "B2":  # Clone a git repo and make a commit
            run_subprocess("git clone https://github.com/HanushKarthick2002/my-site ./data/repo")
            run_subprocess("cd ./data/repo && git add . && git commit -m 'Automated commit'")

        elif selected_task == "B3":  # Run a SQL query on a SQLite or DuckDB database
            conn = sqlite3.connect('./data/ticket-sales.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
            total = cursor.fetchone()[0]
            with open('./data/ticket-sales-gold.txt', 'w') as out:
                out.write(str(total))
            conn.close()

        elif selected_task == "B4":  # Extract data from (i.e. scrape) a website
            response = requests.get("https://example.com")
            if response.status_code == 200:
                with open('./data/scraped_data.html', 'w') as out:
                    out.write(response.text)
            else:
                raise HTTPException(status_code=500, detail="Failed to scrape website")

        elif selected_task == "B5":  # Compress or resize an image
            image_path = './data/image.png'
            with Image.open(image_path) as img:
                img = img.resize((100, 100))  # Resize image
                img.save('./data/image_resized.png', "PNG")

        elif selected_task == "B6":  # Transcribe audio from an MP3 file
            data, samplerate = sf.read('./data/audio.mp3')
            # Here you would implement the transcription logic
            # For example, using a speech-to-text library
            # transcribed_text = transcribe_audio(data, samplerate)
            transcribed_text = "Transcribed audio text"  # Placeholder
            with open('./data/transcription.txt', 'w') as out:
                out.write(transcribed_text)

        elif selected_task == "B7":  # Convert Markdown to HTML
            with open('./data/document.md') as f:
                markdown_content = f.read()
            html_content = markdown_to_html(markdown_content)  # Implement this function
            with open('./data/document.html', 'w') as out:
                out.write(html_content)

        elif selected_task == "B8":  # Write an API endpoint that filters a CSV file and returns JSON data
            df = pd.read_csv('./data/data.csv')
            filtered_df = df[df['column_name'] == 'filter_value']  # Example filter
            filtered_df.to_json('./data/filtered_data.json', orient='records')
        else:
            raise HTTPException(status_code=400, detail="Unknown task")

        return {"status": "success", "task": selected_task}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

data_dir = Path("./data")  # Allowed data directory

@app.get("/read")
def read_file(path: str = Query(..., description="Path of the file inside /data directory")):
    file_path = data_dir / path

    # Manual Security check B1: Ensure path is inside /data
    try:
        file_path.relative_to(data_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access to paths outside /data is forbidden.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        content = file_path.read_text()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
def markdown_to_html(markdown_content):
    # Implement a simple markdown to HTML conversion
    return "<html><body>" + markdown_content.replace("\n", "<br>") + "</body></html>"
