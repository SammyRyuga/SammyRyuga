"""Render an activity chart from GitHub's real contribution calendar; no dependencies."""
import datetime as dt
import json
import math
import os
from pathlib import Path
import urllib.request

now = dt.datetime.now(dt.timezone.utc)
start = (now - dt.timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
query = '''query($from: DateTime!, $to: DateTime!) {
  user(login: "SammyRyuga") {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}'''
request = urllib.request.Request(
    'https://api.github.com/graphql',
    data=json.dumps({'query': query, 'variables': {'from': start.isoformat(), 'to': now.isoformat()}}).encode(),
    headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Content-Type': 'application/json', 'User-Agent': 'SammyRyuga-profile'},
)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)
if result.get('errors'):
    raise RuntimeError(result['errors'])
weeks = result['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
counts = {d['date']: d['contributionCount'] for w in weeks for d in w['contributionDays']}
dates = [(start + dt.timedelta(days=i)).date() for i in range(31)]
values = [counts.get(d.isoformat(), 0) for d in dates]
ceiling = max(4, math.ceil(max(values) / 4) * 4)
left, right, top, bottom = 58, 950, 98, 235
points = [(left + i * (right-left)/30, bottom - n*(bottom-top)/ceiling) for i, n in enumerate(values)]
path = ' '.join(('M' if i == 0 else 'L') + f'{x:.1f},{y:.1f}' for i, (x, y) in enumerate(points))
svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="300" viewBox="0 0 1000 300" role="img" aria-labelledby="title desc">
<title id="title">Samanyu's GitHub activity — last 31 days</title>
<desc id="desc">{sum(values)} contributions between {dates[0]} and {dates[-1]}. Generated from GitHub's contribution calendar.</desc>
<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#7dd3fc" stop-opacity=".3"/><stop offset="1" stop-color="#7dd3fc" stop-opacity=".02"/></linearGradient></defs>
<rect x="1" y="1" width="998" height="298" rx="14" fill="#0d1117" stroke="#293449"/>
<g font-family="Segoe UI,Arial,sans-serif">
<text x="32" y="39" font-size="21" font-weight="600" fill="#f0f6fc">Small steps. Real progress.</text>
<text x="32" y="65" font-size="13" fill="#94a3b8">{sum(values)} contributions · {sum(v > 0 for v in values)} active days · last 31 days</text>
<text x="968" y="40" text-anchor="end" font-size="12" fill="#c4b5fd">@SammyRyuga</text>'''.replace('&gt;', '>')]
for i in range(5):
    value = ceiling*i/4
    y = bottom - (bottom-top)*i/4
    svg.append(f'<path d="M{left} {y}H{right}" stroke="#212c3d" stroke-dasharray="3 6"/><text x="42" y="{y+4}" text-anchor="end" font-size="11" fill="#94a3b8">{int(value)}</text>')
svg.append(f'<path d="{path} L{right},{bottom} L{left},{bottom}Z" fill="url(#area)"/><path d="{path}" stroke="#7dd3fc" stroke-width="2.5" stroke-linejoin="round" fill="none"/>')
for (x,y), date, value in zip(points, dates, values):
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#c4b5fd" stroke="#0d1117" stroke-width="1.5"><title>{date}: {value} contributions</title></circle>')
for i in (0, 6, 12, 18, 24, 30):
    svg.append(f'<text x="{points[i][0]:.1f}" y="262" text-anchor="middle" font-size="11" fill="#94a3b8">{dates[i].strftime("%d %b")}</text>')
svg.append(f'<text x="968" y="284" text-anchor="end" font-size="10" fill="#64748b">Updated {now.strftime("%d %b %Y")} UTC</text></g></svg>')
Path('assets').mkdir(exist_ok=True)
Path('assets/activity.svg').write_text('\n'.join(svg), encoding='utf-8')
