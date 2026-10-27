"""把 ComfyUI index.html 里的 ./assets/ 引用切换到 jsDelivr CDN。

用法：
    python apply_cdn.py --sha 8ddbed7d525c47c56973c27ce992854ddda64f90   切到 CDN
    python apply_cdn.py --revert                                         切回本地
    python apply_cdn.py --check                                          查看当前状态

只替换 ./assets/ 前缀，不动 /api/、/extensions/、user.css 等本地路径。
首次运行时自动生成 index.html.bak；--revert 从该备份恢复。
"""
import argparse
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INDEX = (r"D:\comFyui\python_embeded\Lib\site-packages"
         r"\comfyui_frontend_package\static\index.html")
BACKUP = INDEX + ".bak"

REPO = "xiaolongmr/comfyui-frontend-cdn"
# 接入点：cdn.jsdelivr.net 在本网络 1/12 成功率（TLS 被重置），必须用备用接入点。
# 实测 fastly / testingcf / gcore 均 12/12 成功，平均 0.6-0.7s。
DEFAULT_HOST = "fastly.jsdelivr.net"
CDN_TEMPLATE = "https://{host}/gh/{repo}@{sha}/assets/"

# 任意 jsDelivr 接入点都算「已切换」，方便换 host 时批量替换
ANY_CDN = r'https://[a-z0-9.-]*jsdelivr[a-z0-9.-]*/gh/' + re.escape(REPO) + r'@[0-9a-f]+/assets/'

PREFIX_RE = re.compile(r'(?:\./assets/|' + ANY_CDN + r')')

# PWA manifest 必须留在同源：它在 index.html 里带 crossorigin="use-credentials"，
# 浏览器会以 credentials mode = include 请求，而 jsDelivr 只能返回 ACAO: *，
# 规范禁止 wildcard 配 credentials，请求会被 CORS 直接拦掉。
KEEP_LOCAL_RE = re.compile(
    r'https://[a-z0-9.-]*jsdelivr[a-z0-9.-]*/gh/' + re.escape(REPO)
    + r'@[0-9a-f]+/assets/(manifest-[A-Za-z0-9_-]+\.json)'
)


def read_html():
    with open(INDEX, "r", encoding="utf-8") as f:
        return f.read()


def show_state():
    html = read_html()
    matches = sorted(set(PREFIX_RE.findall(html)))
    print("=== 当前 index.html 的 assets 引用前缀 ===")
    for m in matches:
        print(f"  {m}")
    print(f"=== ./assets/ 出现次数: {html.count('./assets/')} ===")
    hosts = sorted(set(re.findall(r'https://([a-z0-9.-]*jsdelivr[a-z0-9.-]*)/gh/', html)))
    print(f"=== 当前 CDN 接入点: {hosts or '（未切换）'} ===")
    print(f"=== 备份文件存在: {os.path.exists(BACKUP)} ===")
    bad = KEEP_LOCAL_RE.findall(html)
    if bad:
        print(f"[警告] manifest 被指到了 CDN（会触发 CORS 报错，必须留本地）: {bad}")
    else:
        print("[OK] manifest 仍在本地（同源）")


def apply(sha, host=DEFAULT_HOST):
    if not os.path.exists(BACKUP):
        shutil.copy2(INDEX, BACKUP)
        print(f"[备份] {BACKUP}")
    else:
        print(f"[备份] 已存在，保留原样: {BACKUP}")

    html = read_html()
    cdn = CDN_TEMPLATE.format(host=host, repo=REPO, sha=sha)
    new_html, n = PREFIX_RE.subn(cdn, html)
    if n == 0:
        print("[跳过] 没有找到 assets 引用，文件可能已是目标状态")
        return
    # 事后纠正：把 manifest-*.json 拉回 ./assets/，保证同源
    new_html, m = KEEP_LOCAL_RE.subn(r'./assets/\1', new_html)
    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        f.write(new_html)
    print(f"[完成] 已替换 {n} 处 -> {cdn}")
    if m:
        print(f"[保护] manifest 已回退为本地同源引用（{m} 处）")
    show_state()


def revert():
    if not os.path.exists(BACKUP):
        print("[失败] 备份不存在，无法回滚")
        return
    shutil.copy2(BACKUP, INDEX)
    print(f"[回滚] 已从 {BACKUP} 恢复")
    show_state()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", help="jsDelivr 使用的 commit SHA")
    ap.add_argument("--host", default=DEFAULT_HOST,
                    help=f"接入点，默认 {DEFAULT_HOST}；可选 testingcf.jsdelivr.net / gcore.jsdelivr.net")
    ap.add_argument("--revert", action="store_true", help="回滚到本地引用")
    ap.add_argument("--check", action="store_true", help="只查看当前状态")
    args = ap.parse_args()

    if not os.path.exists(INDEX):
        print(f"[失败] 找不到 {INDEX}")
        return

    if args.revert:
        revert()
    elif args.sha:
        apply(args.sha, args.host)
    else:
        show_state()


if __name__ == "__main__":
    main()
