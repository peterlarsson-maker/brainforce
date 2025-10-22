import os
import subprocess
import shutil
from datetime import datetime

def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def red(text): return f"\033[91m{text}\033[0m"
def bold(text): return f"\033[1m{text}\033[0m"

def print_status(label, exists):
    print(f"{label.ljust(32)}", end="")
    print(green("✔ Finns") if exists else red("✗ Saknas"))

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def file_exists(path): return os.path.exists(path)
def folder_exists(path): return os.path.isdir(path)
def list_subfolders(base_path):
    return [d for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))
            and not d.startswith('.') and d not in ("__pycache__", "venv", "env", "node_modules", "status")]

def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def get_git_remote():
    if not folder_exists(".git"):
        return None
    result = run("git remote -v")
    remotes = set()
    for line in result.stdout.splitlines():
        if line.strip():
            remotes.add(line.split()[1])
    return remotes if remotes else None

def is_git_repo():
    return folder_exists(".git")

# ====== MALLAR ======
README_MD = """# README

Denna mapp tillhör projektet.  
Fyll på beskrivning och syfte här!
"""

GITIGNORE = """# Python
venv/
__pycache__/
*.pyc

# Node
node_modules/
dist/
build/

# VS Code/OS/editor
.vscode/
.DS_Store
Thumbs.db
.env

# Automatisk status/backup
status/
"""

REQUIREMENTS = """# Lägg till Python-beroenden här, ex:
# fastapi
# openai
"""

PACKAGE_JSON = """{
  "name": "projekt-namn",
  "version": "1.0.0",
  "main": "index.js",
  "license": "MIT"
}
"""

# ====== 1. FLYTTA TILL PROJEKTROT ======
def byt_till_projektrot():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

# ====== 2. STATUSKONTROLL & ÅTGÄRDER ======
def kontroll_och_fix():
    log = []
    print(bold("\n=== PROJEKTSTATUSKONTROLL ===\n"))
    log.append("# Projektstatus\n")

    # Kontrollera/lagra viktigaste filer
    files_to_check = {
        "README.md": file_exists("README.md"),
        ".gitignore": file_exists(".gitignore"),
        "requirements.txt": file_exists("requirements.txt"),
        "package.json": file_exists("package.json"),
    }
    dirs_to_check = {
        "venv/": folder_exists("venv"),
        "env/": folder_exists("env"),
        "node_modules/": folder_exists("node_modules"),
    }
    git_repo = is_git_repo()
    remote = get_git_remote() if git_repo else None

    print("Fil-/mappstatus:")
    log.append("## Fil-/mappstatus\n")
    for fname, exists in files_to_check.items():
        print_status(fname, exists)
        log.append(f"- {fname}: {'OK' if exists else 'Saknas'}")
    for dname, exists in dirs_to_check.items():
        print_status(dname, exists)
        log.append(f"- {dname}: {'OK' if exists else 'Saknas'}")
    print_status("Git-repo (.git)", git_repo)
    print_status("Git remote", remote is not None)
    log.append(f"- Git-repo: {'OK' if git_repo else 'Saknas'}")
    log.append(f"- Git remote: {'OK' if remote else 'Saknas'}")

    todo = []

    # Skapa .gitignore om saknas
    if not files_to_check[".gitignore"]:
        write_file(".gitignore", GITIGNORE)
        print(green("Skapade .gitignore"))
        log.append("- Skapade .gitignore")
    else:
        with open(".gitignore", "r", encoding="utf-8") as f:
            ignore_content = f.read()
        if "status/" not in ignore_content:
            with open(".gitignore", "a", encoding="utf-8") as f:
                f.write("\nstatus/\n")
            print(yellow("Lade till 'status/' i .gitignore"))
            log.append("- Lade till 'status/' i .gitignore")

    # Skapa README.md i root om saknas
    if not files_to_check["README.md"]:
        write_file("README.md", README_MD)
        print(green("Skapade README.md"))
        log.append("- Skapade README.md")

    # Skapa requirements.txt om Pythonprojekt och saknas
    if (dirs_to_check["venv/"] or dirs_to_check["env/"]) and not files_to_check["requirements.txt"]:
        write_file("requirements.txt", REQUIREMENTS)
        print(green("Skapade requirements.txt"))
        log.append("- Skapade requirements.txt")
    # Skapa package.json om node-projekt och saknas
    if dirs_to_check["node_modules/"] and not files_to_check["package.json"]:
        write_file("package.json", PACKAGE_JSON)
        print(green("Skapade package.json"))
        log.append("- Skapade package.json")

    # Initiera git repo om saknas
    if not git_repo:
        run("git init")
        print(green("Initierade git repo"))
        log.append("- Initierade git repo")
        todo.append("Lägg till remote till GitHub")

    # README i alla undermappar
    for sub in list_subfolders("."):
        sub_readme = os.path.join(sub, "README.md")
        if not file_exists(sub_readme):
            write_file(sub_readme, f"# README\n\nDenna mapp ({sub}) tillhör projektet. Fyll på beskrivning!")
            print(yellow(f"Skapade README.md i {sub}/"))
            log.append(f"- Skapade README.md i {sub}/")
    
    # Remote-kontroll
    if git_repo and not remote:
        todo.append("Lägg till git remote-url (GitHub)")

    # TODO-lista
    if todo:
        print(yellow("\nAtt göra:"))
        log.append("\n## Att göra\n")
        for t in todo:
            print("- " + t)
            log.append("- " + t)
    else:
        print(green("\nProjektet är komplett och redo att commit:a och pusha!"))
        log.append("\nProjektet är klart.")

    return log

# ====== 3. BACKUP AV PROJEKT ======
def backup():
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = os.path.join("status", "backup")
    os.makedirs(backup_root, exist_ok=True)
    backupdir = os.path.join(backup_root, f"backup_{now}")
    os.makedirs(backupdir, exist_ok=True)
    exclude = ["venv", "env", "node_modules", "status", ".git", "__pycache__"]

    print(bold(f"\nBackup: Kopierar projekt till {backupdir} ..."))

    for item in os.listdir("."):
        if item in exclude:
            continue
        s = os.path.join(".", item)
        d = os.path.join(backupdir, item)
        try:
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        except Exception as e:
            print(red(f"Kunde inte kopiera {item}: {e}"))

    print(green(f"Backup klar i: {backupdir}"))
    return backupdir

# ====== 4. LOGGA RESULTAT ======
def logga(lograd, backupdir):
    logdir = os.path.join("status", "log")
    os.makedirs(logdir, exist_ok=True)
    logfil = os.path.join(logdir, "status-log.txt")
    with open(logfil, "a", encoding="utf-8") as f:
        f.write(f"\n\n# Ny körning {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for row in lograd:
            f.write(row + "\n")
        f.write(f"\nBackup: {backupdir}\n")

# ====== MAIN ======
if __name__ == "__main__":
    byt_till_projektrot()
    log = kontroll_och_fix()
    backupdir = backup()
    logga(log, backupdir)
    print(bold("\n--- KLART! Allt loggat och backup sparad. ---\n"))

