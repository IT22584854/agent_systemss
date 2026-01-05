import os
import shutil

# Paths
md_dir = "0_raw_data/markdown"
junk_dir = "0_raw_data/markdown_junk"

if not os.path.exists(junk_dir):
    os.makedirs(junk_dir)

print("🧹 Starting Force Cleanup...")

# 1. Remove small "Junk" files (< 500 bytes)
files = os.listdir(md_dir)
small_count = 0
for file in files:
    path = os.path.join(md_dir, file)
    if os.path.isfile(path) and os.path.getsize(path) < 500:
        shutil.move(path, os.path.join(junk_dir, file))
        small_count += 1

# 2. Remove Duplicates (Exact same size)
remaining_files = os.listdir(md_dir)
seen_sizes = {}
dup_count = 0
for file in remaining_files:
    path = os.path.join(md_dir, file)
    if os.path.isfile(path):
        size = os.path.getsize(path)
        if size in seen_sizes:
            shutil.move(path, os.path.join(junk_dir, file))
            dup_count += 1
        else:
            seen_sizes[size] = file

print(f"✅ Small files moved: {small_count}")
print(f"✅ Duplicates moved: {dup_count}")
print(f"🚀 Total Unique Files remaining: {len(os.listdir(md_dir))}")