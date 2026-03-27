import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(BASE_DIR, "-BG-ALL")

if not os.path.exists(DEST_DIR):
    print(f"Папка {DEST_DIR} не найдена")
    exit()

copied = 0
skipped = 0

for root, dirs, files in os.walk(BASE_DIR):
    if os.path.basename(root) == "BG":
        best_path = os.path.join(root, "BEST")

        # Если есть BEST → берем только из нее
        if os.path.isdir(best_path):
            source_files = [
                f for f in os.listdir(best_path)
                if f.lower().endswith(".html")
            ]
            source_dir = best_path
        else:
            source_files = [
                f for f in files
                if f.lower().endswith(".html")
            ]
            source_dir = root

        for file in source_files:
            src_path = os.path.join(source_dir, file)
            dest_path = os.path.join(DEST_DIR, file)

            if os.path.exists(dest_path):
                skipped += 1
                continue

            shutil.copy2(src_path, dest_path)
            copied += 1

print(f"Готово! Скопировано: {copied}, пропущено (дубликаты): {skipped}")
