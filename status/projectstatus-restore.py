import os
import shutil
from datetime import datetime

def bold(txt): return f"\033[1m{txt}\033[0m"
def green(txt): return f"\033[92m{txt}\033[0m"
def yellow(txt): return f"\033[93m{txt}\033[0m"
def red(txt): return f"\033[91m{txt}\033[0m"

def list_backups(backup_root="status/backup"):
    backups = []
    if not os.path.exists(backup_root):
        return []
    for d in os.listdir(backup_root):
        full = os.path.join(backup_root, d)
        if d.startswith("backup_") and os.path.isdir(full):
            backups.append(d)
    return sorted(backups, reverse=True)

def confirm(msg):
    return input(f"{msg} [j/n]: ").strip().lower().startswith("j")

def main():
    # Byt till projektrot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    print(bold("\n=== ÅTERSTÄLLNING FRÅN BACKUP ===\n"))
    backups = list_backups("status/backup")
    if not backups:
        print(red("Ingen backup hittades!"))
        return

    print("Tillgängliga backups:")
    for i, b in enumerate(backups):
        print(f"{i+1}. {b}")

    val = input(f"Ange nummer på backup som ska återställas [1-{len(backups)}] (enter för senaste): ").strip()
    if not val:
        idx = 0
    else:
        try:
            idx = int(val)-1
            if idx < 0 or idx >= len(backups):
                print(red("Felaktigt nummer!"))
                return
        except:
            print(red("Felaktig inmatning!"))
            return

    backupdir = os.path.join("status", "backup", backups[idx])
    print(yellow(f"\nVald backup: {backupdir}"))
    if not confirm("Detta skriver över alla aktuella projektfiler utom status/, .git/, venv/ osv. Är du säker?"):
        print("Avbruten.")
        return

    exclude = ["status", ".git", "venv", "env", "node_modules", "__pycache__"]
    for item in os.listdir(backupdir):
        if item in exclude:
            continue
        src = os.path.join(backupdir, item)
        dst = os.path.join(".", item)
        try:
            if os.path.isdir(src):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(green(f"Återställde: {item}"))
        except Exception as e:
            print(red(f"Fel vid återställning av {item}: {e}"))

    print(bold("\nÅterställning klar!"))
    print(green("Nu är projektet tillbaka till valt backup-läge.\n"))

if __name__ == "__main__":
    main()
