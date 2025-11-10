import subprocess
import sys
import os

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.check_call(cmd, shell=True)

# 1. Create venv
run("python -m venv .venv")

# 2. Activate venv (Windows)
venv_python = r".venv\Scripts\python.exe"
pip = rf".venv\Scripts\pip.exe"

# 3. Install requirements
run(f"{pip} install -r requirements.txt")

# 4. Run Django migrations
run(f"{venv_python} manage.py migrate")

# 5. Seed demo data
run(f"{venv_python} manage.py seed_demo")

# 6. Run server
run(f"{venv_python} manage.py runserver")
