"""统计 ComfyUI 前端 assets 目录，并把要上 CDN 的文件复制到本地仓库目录。

排除 .map（source map，浏览器正常不请求），其余按原目录结构保留。
"""
import os
import shutil
import sys
from collections import defaultdict

SRC = r"D:\comFyui\python_embeded\Lib\site-packages\comfyui_frontend_package\static\assets"
DST = r"D:\Tool\comfyui-cdn\assets"

SKIP_EXT = {".map"}

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

stats = defaultdict(lambda: [0, 0])
total_files = total_bytes = 0
skipped_files = skipped_bytes = 0

for root, _dirs, files in os.walk(SRC):
    for name in files:
        path = os.path.join(root, name)
        ext = os.path.splitext(name)[1].lower()
        size = os.path.getsize(path)
        if ext in SKIP_EXT:
            skipped_files += 1
            skipped_bytes += size
            continue
        stats[ext][0] += 1
        stats[ext][1] += size
        total_files += 1
        total_bytes += size

print("=== assets 目录统计（排除 .map）===")
for ext in sorted(stats, key=lambda e: -stats[e][1]):
    n, b = stats[ext]
    print(f"  {ext or '(无扩展名)':10} {n:5} 个   {b/1024/1024:8.2f} MB")
print(f"  {'合计':10} {total_files:5} 个   {total_bytes/1024/1024:8.2f} MB")
print(f"  跳过 .map   {skipped_files:5} 个   {skipped_bytes/1024/1024:8.2f} MB")

if "--copy" not in sys.argv:
    print("\n(仅统计，加 --copy 才复制)")
    sys.exit(0)

if os.path.isdir(DST):
    shutil.rmtree(DST)
copied = copied_bytes = 0
for root, _dirs, files in os.walk(SRC):
    for name in files:
        if os.path.splitext(name)[1].lower() in SKIP_EXT:
            continue
        src_path = os.path.join(root, name)
        rel = os.path.relpath(src_path, SRC)
        dst_path = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src_path, dst_path)
        copied += 1
        copied_bytes += os.path.getsize(dst_path)

print(f"\n=== 已复制到 {DST} ===")
print(f"  {copied} 个文件，{copied_bytes/1024/1024:.2f} MB")
