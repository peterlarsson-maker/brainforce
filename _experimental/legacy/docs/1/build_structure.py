import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Användning: python build_structure.py <filnamn>")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print("Filen hittades inte:", src_path)
        sys.exit(1)

    base_dir = Path.cwd()
    current_file = None
    buffer = []
    created = []

    def flush():
        nonlocal buffer, current_file
        if current_file and buffer:
            dest = base_dir / current_file
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write("".join(buffer).strip() + "\n")
            created.append(str(dest.relative_to(base_dir)))
            buffer = []

    with open(src_path, "r", encoding="utf-8") as src:
        for line in src:
            if line.startswith("# brainforce/"):
                flush()
                current_file = Path(line.strip("# \n"))
                continue
            if current_file:
                buffer.append(line)

    flush()

    print("\n🧠 Klart!")
    print(f"Filer skapade: {len(created)}")
    for f in created:
        print(" -", f)

if __name__ == "__main__":
    main()