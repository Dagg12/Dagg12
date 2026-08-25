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
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "login": USERNAME,
        "from": start.isoformat(),
        "to": end.isoformat(),
    },
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Dagg12-profile-streak-generator",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)

if data.get("errors"):
    raise RuntimeError(json.dumps(data["errors"]))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
counts = {day["date"]: day["contributionCount"] for day in days}

# Calculate streaks using GitHub's contribution calendar dates.
ordered_dates = sorted(counts)
longest = 0
run = 0
previous = None
for date_text in ordered_dates:
    current = datetime.strptime(date_text, "%Y-%m-%d").date()
    if counts[date_text] > 0 and previous is not None and current == previous + timedelta(days=1):
        run += 1
    elif counts[date_text] > 0:
        run = 1
    else:
        run = 0
    longest = max(longest, run)
    previous = current

# Current streak ends today when there is activity today; otherwise it ends yesterday.
today = now.date()
anchor = today if counts.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
current_streak = 0
cursor = anchor
while counts.get(cursor.isoformat(), 0) > 0:
    current_streak += 1
    cursor -= timedelta(days=1)


def esc(value):
    return escape(str(value))

width, height = 1000, 285
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Dagg12 GitHub contribution streak</title>
<desc id="desc">GitHub contribution statistics for Dagg12, including total contributions, current streak and longest streak.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0b1220"/>
    <stop offset="100%" stop-color="#111827"/>
  </linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#00e5ff"/>
    <stop offset="100%" stop-color="#8b5cf6"/>
  </linearGradient>
</defs>
<rect x="1" y="1" width="998" height="283" rx="20" fill="url(#bg)" stroke="#263247"/>
<rect x="0" y="0" width="1000" height="5" rx="3" fill="url(#accent)"/>
<text x="44" y="52" fill="#f8fafc" font-family="Arial, Helvetica, sans-serif" font-size="25" font-weight="700">🔥 Dagg12 GitHub Streak</text>
<text x="44" y="78" fill="#94a3b8" font-family="Arial, Helvetica, sans-serif" font-size="14">Live contribution data • generated automatically by GitHub Actions</text>

<rect x="44" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/>
<rect x="362" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/>
<rect x="680" y="105" width="275" height="125" rx="16" fill="#111c2f" stroke="#24334d"/>

<text x="68" y="139" fill="#94a3b8" font-family="Arial, Helvetica, sans-serif" font-size="14">TOTAL CONTRIBUTIONS</text>
<text x="68" y="190" fill="#00e5ff" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="700">{esc(calendar['totalContributions'])}</text>
<text x="68" y="214" fill="#64748b" font-family="Arial, Helvetica, sans-serif" font-size="12">last 12 months</text>

<text x="386" y="139" fill="#94a3b8" font-family="Arial, Helvetica, sans-serif" font-size="14">CURRENT STREAK</text>
<text x="386" y="190" fill="#8b5cf6" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="700">{esc(current_streak)}</text>
<text x="386" y="214" fill="#64748b" font-family="Arial, Helvetica, sans-serif" font-size="12">consecutive days</text>

<text x="704" y="139" fill="#94a3b8" font-family="Arial, Helvetica, sans-serif" font-size="14">LONGEST STREAK</text>
<text x="704" y="190" fill="#00ff9d" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="700">{esc(longest)}</text>
<text x="704" y="214" fill="#64748b" font-family="Arial, Helvetica, sans-serif" font-size="12">consecutive days</text>

<text x="500" y="260" text-anchor="middle" fill="#475569" font-family="Arial, Helvetica, sans-serif" font-size="11">DAGG12 • BUILD • COMMIT • REPEAT</text>
</svg>
'''

os.makedirs("profile", exist_ok=True)
with open("profile/streak.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print(f"Generated profile/streak.svg — total={calendar['totalContributions']}, current={current_streak}, longest={longest}")
