import os
from datetime import datetime
import subprocess

def green(text): return f"\033[92m{text}\033[0m"

def read_file(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return "*Saknas*"

def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def get_git_info():
    if not os.path.isdir("../.git"):
        return "*Inget git-repo initierat*"
    branch = run("git rev-parse --abbrev-ref HEAD")
    remote = run("git remote -v")
    lastcommit = run("git log -1 --oneline")
    out = [
        f"Branch: {branch.stdout.strip()}",
        f"Remote:\n{remote.stdout.strip()}",
        f"Senaste commit:\n{lastcommit.stdout.strip()}"
    ]
    return "\n".join(out)

def main():
    # Byt till projektrot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    os.chdir(project_root)

    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    status_log = read_file(os.path.join("status", "log", "status-log.txt"))
    readme_root = read_file("README.md")
    reqs = read_file("requirements.txt")
    pkg = read_file("package.json")
    gitinfo = get_git_info()

    todo = []
    if "Att göra" in status_log:
        todo = status_log.split("Att göra")[1].split("Backup")[0].strip().split("\n")
    elif "Att göra" in status_log:
        todo = status_log.split("Att göra")[1].split("\n")
    else:
        todo = ["(Inga TODO just nu)"]

    # Skapa mapp för tradstart om ej finns
    tradstartdir = os.path.join("status", "tradstart")
    os.makedirs(tradstartdir, exist_ok=True)
    tradstartfil = os.path.join(tradstartdir, f"tradstart_{now}.md")

    with open(tradstartfil, "w", encoding="utf-8") as f:
        f.write(f"# Trådstart för projekt\n\n")
        f.write(f"**Datum/tid:** {now}\n\n")
        f.write(f"## Projektets README\n\n{readme_root}\n\n")
        f.write(f"## Git-status\n\n{gitinfo}\n\n")
        f.write(f"## Python beroenden (`requirements.txt`)\n\n{reqs}\n\n")
        f.write(f"## Node beroenden (`package.json`)\n\n{pkg}\n\n")
        f.write(f"## Status & TODO-lista\n\n{status_log}\n\n")
        f.write(f"---\n")
        f.write("*(Denna fil är skapad automatiskt av tradstart.py – bara dra in i ny tråd eller dela!)*\n")

    print(green(f"\nTrådstart skapad: {tradstartfil}\n"))

if __name__ == "__main__":
    main()
