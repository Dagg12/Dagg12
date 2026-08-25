import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

USERNAME = "Dagg12"
TOKEN = os.environ["GITHUB_TOKEN"]
now = datetime.now(timezone.utc)
end = now
start = end - timedelta(days=365)

query = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""
payload = json.dumps({"query": query, "variables": {"login": USERNAME, "from": start.isoformat(), "to": end.isoformat()}}).encode()
request = urllib.request.Request(
    "https://api.github.com/graphql", data=payload,
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "Dagg12-profile-stats"}, method="POST")
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)
if data.get("errors"):
    raise RuntimeError(json.dumps(data["errors"]))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
counts = {day["date"]: day["contributionCount"] for day in days}

# Streak calculations
longest = run = 0
previous = None
for date_text in sorted(counts):
    current = datetime.strptime(date_text, "%Y-%m-%d").date()
    if counts[date_text] > 0 and previous is not None and current == previous + timedelta(days=1):
        run += 1
    elif counts[date_text] > 0:
        run = 1
    else:
        run = 0
    longest = max(longest, run)
    previous = current

today = now.date()
anchor = today if counts.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
current_streak = 0
cursor = anchor
while counts.get(cursor.isoformat(), 0) > 0:
    current_streak += 1
    cursor -= timedelta(days=1)

os.makedirs("profile", exist_ok=True)

def esc(v): return escape(str(v))

def svg_card(title, subtitle, body, width=1000, height=320):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#0b1220"/><stop offset="100%" stop-color="#111827"/></linearGradient><linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#00e5ff"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
<rect x="1" y="1" width="998" height="318" rx="20" fill="url(#bg)" stroke="#263247"/><rect width="1000" height="5" rx="3" fill="url(#accent)"/>
<text x="44" y="48" fill="#f8fafc" font-family="Arial" font-size="25" font-weight="700">{title}</text>
<text x="44" y="73" fill="#94a3b8" font-family="Arial" font-size="14">{subtitle}</text>{body}</svg>'''

body = f'''
<rect x="44" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/><rect x="362" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/><rect x="680" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/>
<text x="68" y="139" fill="#94a3b8" font-family="Arial" font-size="14">TOTAL CONTRIBUTIONS</text><text x="68" y="190" fill="#00e5ff" font-family="Arial" font-size="42" font-weight="700">{calendar['totalContributions']}</text><text x="68" y="214" fill="#64748b" font-family="Arial" font-size="12">last 12 months</text>
<text x="386" y="139" fill="#94a3b8" font-family="Arial" font-size="14">CURRENT STREAK</text><text x="386" y="190" fill="#8b5cf6" font-family="Arial" font-size="42" font-weight="700">{current_streak}</text><text x="386" y="214" fill="#64748b" font-family="Arial" font-size="12">consecutive days</text>
<text x="704" y="139" fill="#94a3b8" font-family="Arial" font-size="14">LONGEST STREAK</text><text x="704" y="190" fill="#00ff9d" font-family="Arial" font-size="42" font-weight="700">{longest}</text><text x="704" y="214" fill="#64748b" font-family="Arial" font-size="12">consecutive days</text>
<text x="500" y="270" text-anchor="middle" fill="#475569" font-family="Arial" font-size="11">DAGG12 • BUILD • COMMIT • REPEAT</text>'''
with open("profile/streak.svg", "w", encoding="utf-8") as f:
    f.write(svg_card("🔥 Dagg12 GitHub Streak", "Live contribution data • generated automatically by GitHub Actions", body))

# Monthly contribution graph: 12 complete/current months.
months = []
base = today.replace(day=1)
for i in range(11, -1, -1):
    y, m = base.year, base.month - i
    while m <= 0: y -= 1; m += 12
    months.append((y, m))
monthly = []
for y, m in months:
    total = sum(v for d, v in counts.items() if datetime.strptime(d, "%Y-%m-%d").year == y and datetime.strptime(d, "%Y-%m-%d").month == m)
    monthly.append((datetime(y, m, 1).strftime("%b"), total))
max_total = max([v for _, v in monthly] + [1])
bar_parts = []
for i, (label, value) in enumerate(monthly):
    x = 70 + i * 75
    h = max(4, int(145 * value / max_total))
    y = 235 - h
    bar_parts.append(f'<rect x="{x}" y="{y}" width="42" height="{h}" rx="6" fill="#00e5ff" opacity="0.82"/><text x="{x+21}" y="258" text-anchor="middle" fill="#94a3b8" font-family="Arial" font-size="12">{label}</text><text x="{x+21}" y="{y-7}" text-anchor="middle" fill="#e2e8f0" font-family="Arial" font-size="11">{value}</text>')
activity_body = '<line x1="58" y1="235" x2="955" y2="235" stroke="#263247"/>' + ''.join(bar_parts) + '<text x="58" y="125" fill="#64748b" font-family="Arial" font-size="12">COMMITS / CONTRIBUTIONS</text>'
with open("profile/activity.svg", "w", encoding="utf-8") as f:
    f.write(svg_card("📈 Dagg12 Contribution Activity", "Monthly contribution trend across the last 12 months", activity_body, height=320))

print(f"Generated profile/streak.svg and profile/activity.svg — total={calendar['totalContributions']}, current={current_streak}, longest={longest}")
