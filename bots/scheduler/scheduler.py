from apscheduler.schedulers.blocking import BlockingScheduler
import json, subprocess, pathlib
from datetime import datetime

sched = BlockingScheduler()
events = json.load(open("events.json", encoding="utf-8"))["events"]

def job(event):
    subprocess.Popen(["python", "mi_script_accion.py", json.dumps(event)])

for ev in events:
    run_date = datetime.fromisoformat(ev["datetime"])
    sched.add_job(job, 'date', run_date=run_date, args=[ev], id=ev["phase"])

sched.start()