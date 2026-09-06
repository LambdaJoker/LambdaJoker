#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 GitHub 个人主页用的统计 SVG。

为什么需要它：github-readme-stats.vercel.app / github-readme-trophy.vercel.app
在国内网络下经常连不上（curl 返回 000），导致主页大片图片裂开。
这里改成：Actions 里抓 GitHub API -> 本地生成 SVG -> 提交回仓库 -> 用 jsDelivr 加载。
全程不依赖任何第三方渲染服务。

用法：
    GITHUB_TOKEN=xxx python3 scripts/generate_stats.py
输出到 output/ 目录。
"""

import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone

USER = "LambdaJoker"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

LANG_COLORS = {
    "Go": "#00ADD8", "Python": "#3572A5", "Java": "#b07219",
    "JavaScript": "#f1e05a", "TypeScript": "#2b7489", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "Dockerfile": "#384d54",
    "Vue": "#41b883", "C++": "#f34b7d", "C": "#555555", "Rust": "#dea584",
}
FALLBACK_COLOR = "#8b949e"
ACCENT = "#7c5cff"


def api(path):
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-bot"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


FONT = "'Segoe UI','PingFang SC','Microsoft YaHei',Helvetica,Arial,sans-serif"

STYLE = """<style>
.bg{fill:#ffffff;stroke:#d0d7de;stroke-width:1}
.card{fill:#f6f8fa;stroke:#d0d7de;stroke-width:1}
.title{__F__;font-size:15px;font-weight:600;fill:#1f2328}
.label{__F__;font-size:13px;fill:#57606a}
.value{__F__;font-size:13px;font-weight:600;fill:#1f2328}
.muted{__F__;font-size:11px;fill:#8c959f}
.repo{__F__;font-size:14px;font-weight:600;fill:#0969da}
.desc{__F__;font-size:11px;fill:#57606a}
.meta{__F__;font-size:11px;fill:#57606a}
@media (prefers-color-scheme:dark){
.bg{fill:#0d1117;stroke:#30363d}
.card{fill:#161b22;stroke:#30363d}
.title{fill:#c9d1d9}.label{fill:#8b949e}.value{fill:#e6edf3}
.muted{fill:#6e7681}.repo{fill:#58a6ff}.desc{fill:#8b949e}.meta{fill:#8b949e}
}
</style>""".replace("__F__", "font-family:" + FONT)


def dwidth(s):
    """中文按 2 个字符宽度算"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def clip(text, limit):
    """按显示宽度截断，超了加省略号"""
    out, w = "", 0
    for ch in text:
        cw = 2 if ord(ch) > 0x2E80 else 1
        if w + cw > limit:
            return out + "…"
        out += ch
        w += cw
    return out


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="stats">{STYLE}{body}</svg>\n'
    )


# ---------------------------------------------------------------- stats
def build_stats(user, repos, stars, forks):
    rows = [
        ("Total Stars", stars, "#e3b341"),
        ("Total Repos", user["public_repos"], ACCENT),
        ("Total Forks", forks, "#3fb950"),
        ("Followers", user["followers"], "#a371f7"),
        ("Following", user["following"], "#58a6ff"),
        ("Public Gists", user["public_gists"], "#f778ba"),
    ]
    body = ['<rect class="bg" x="0.5" y="0.5" width="479" height="179" rx="10"/>']
    body.append(f'<text class="title" x="24" y="38">{esc(USER)}\'s GitHub Stats</text>')
    body.append('<line x1="24" y1="52" x2="456" y2="52" stroke="#d0d7de" stroke-opacity="0.6"/>')
    for i, (label, val, color) in enumerate(rows):
        col, row = i % 2, i // 2
        x = 24 + col * 224
        y = 84 + row * 34
        body.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>')
        body.append(f'<text class="label" x="{x + 18}" y="{y}">{label}:</text>')
        body.append(f'<text class="value" x="{x + 196}" y="{y}" text-anchor="end">{val}</text>')
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body.append(f'<text class="muted" x="24" y="168">updated {today} · generated locally</text>')
    return svg(480, 180, "".join(body))


# ---------------------------------------------------------------- langs
def build_langs(lang_bytes):
    total = sum(lang_bytes.values()) or 1
    items = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:6]
    h = 62 + len(items) * 30
    body = ['<rect class="bg" x="0.5" y="0.5" width="479" height="%d" rx="10"/>' % (h - 1)]
    body.append('<text class="title" x="24" y="38">Top Languages</text>')
    body.append('<line x1="24" y1="52" x2="456" y2="52" stroke="#d0d7de" stroke-opacity="0.6"/>')
    for i, (name, nb) in enumerate(items):
        pct = nb / total * 100
        y = 76 + i * 30
        color = LANG_COLORS.get(name, FALLBACK_COLOR)
        body.append(f'<text class="label" x="24" y="{y + 4}">{esc(clip(name, 14))}</text>')
        body.append(f'<rect class="card" x="120" y="{y - 6}" width="280" height="10" rx="5"/>')
        body.append(
            f'<rect x="120" y="{y - 6}" width="{max(4, int(280 * pct / 100))}" height="10" rx="5" fill="{color}"/>'
        )
        body.append(f'<text class="muted" x="456" y="{y + 4}" text-anchor="end">{pct:.1f}%</text>')
    return svg(480, h, "".join(body))


# ---------------------------------------------------------------- repos
def build_repos(picked):
    cw, ch, gap, pad = 238, 106, 14, 14
    w = cw * 2 + gap + pad * 2
    h = ch * 2 + gap + pad * 2
    body = [f'<rect class="bg" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10"/>']
    for i, r in enumerate(picked):
        col, row = i % 2, i // 2
        x = pad + col * (cw + gap)
        y = pad + row * (ch + gap)
        body.append(f'<rect class="card" x="{x}" y="{y}" width="{cw}" height="{ch}" rx="8"/>')
        body.append(f'<text class="repo" x="{x + 14}" y="{y + 26}">{esc(clip(r["name"], 22))}</text>')
        desc = r.get("description") or "一个正在生长的项目"
        body.append(f'<text class="desc" x="{x + 14}" y="{y + 46}">{esc(clip(desc, 30))}</text>')
        body.append(f'<text class="desc" x="{x + 14}" y="{y + 62}">{esc(clip(desc[len(clip(desc, 30)) - 1:], 30))}</text>')
        lang = r.get("language") or "—"
        color = LANG_COLORS.get(lang, FALLBACK_COLOR)
        body.append(f'<circle cx="{x + 19}" cy="{y + 84}" r="5" fill="{color}"/>')
        body.append(f'<text class="meta" x="{x + 30}" y="{y + 88}">{esc(lang)}</text>')
        body.append(f'<text class="meta" x="{x + 118}" y="{y + 88}">★ {r["stargazers_count"]}</text>')
        body.append(f'<text class="meta" x="{x + 168}" y="{y + 88}">⑂ {r["forks_count"]}</text>')
    return svg(w, h, "".join(body))


# ---------------------------------------------------------------- milestones
def build_milestones(user, repos, lang_bytes):
    created = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - created).days
    items = [
        ("GitHub 年龄", f"{days // 365} 年", f"{days} 天", ACCENT),
        ("仓库", str(len(repos)), "个原创", "#58a6ff"),
        ("语言", str(len(lang_bytes)), "种在用", "#3fb950"),
        ("最早提交", created.strftime("%Y"), "入坑年份", "#e3b341"),
    ]
    cw, gap, pad = 110, 12, 14
    w = cw * len(items) + gap * (len(items) - 1) + pad * 2
    h = 128
    body = [f'<rect class="bg" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10"/>']
    body.append('<text class="title" x="24" y="38">Milestones</text>')
    body.append('<line x1="24" y1="52" x2="%d" y2="52" stroke="#d0d7de" stroke-opacity="0.6"/>' % (w - 24))
    for i, (label, big, small, color) in enumerate(items):
        x = pad + i * (cw + gap)
        body.append(f'<circle cx="{x + cw / 2}" cy="82" r="26" fill="{color}" fill-opacity="0.15"/>')
        body.append(f'<circle cx="{x + cw / 2}" cy="82" r="26" fill="none" stroke="{color}" stroke-width="1.5"/>')
        body.append(
            f'<text class="value" x="{x + cw / 2}" y="86" text-anchor="middle" font-size="14">{esc(big)}</text>'
        )
        body.append(f'<text x="{x + cw / 2}" y="122" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="11" fill="#8b949e">{esc(label)}</text>')
    return svg(w, h, "".join(body))


def main():
    OUT.mkdir(exist_ok=True)
    user = api("/users/" + USER)
    repos = [r for r in api("/users/%s/repos?per_page=100&type=owner" % USER) if not r["fork"]]

    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)

    lang_bytes = {}
    for r in repos:
        try:
            for k, v in api("/repos/%s/%s/languages" % (USER, r["name"])).items():
                lang_bytes[k] = lang_bytes.get(k, 0) + v
        except Exception as e:
            print("skip languages of", r["name"], e)

    picked = sorted(repos, key=lambda r: r.get("pushed_at") or "", reverse=True)[:4]

    (OUT / "stats.svg").write_text(build_stats(user, repos, stars, forks), encoding="utf-8")
    (OUT / "langs.svg").write_text(build_langs(lang_bytes), encoding="utf-8")
    (OUT / "repos.svg").write_text(build_repos(picked), encoding="utf-8")
    (OUT / "milestones.svg").write_text(build_milestones(user, repos, lang_bytes), encoding="utf-8")

    print("stars=%d forks=%d repos=%d langs=%d" % (stars, forks, len(repos), len(lang_bytes)))
    for f in sorted(OUT.glob("*.svg")):
        print("  ->", f.name, f.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
