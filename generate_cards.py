import os, json, urllib.request
from xml.sax.saxutils import escape

TOKEN = os.environ["GH_TOKEN"]
USER = os.environ["GH_USER"]

BG, GOLD, TEXT, MUTED = "#0D0D0D", "#B89632", "#D6D0C4", "#777777"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection { totalCommitContributions }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    payload = json.load(r)
if "errors" in payload:
    raise SystemExit(payload["errors"])
u = payload["data"]["user"]

repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
total = sum(s for _, s in top) or 1

W, H = 495, 195


def frame(title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>
<text x="30" y="38" font-family="{FONT}" font-size="18" font-weight="600" fill="{GOLD}">{escape(title)}</text>
{body}
</svg>"""


# Stats card
rows = [
    ("Total Stars", stars),
    ("Commits (this year)", u["contributionsCollection"]["totalCommitContributions"]),
    ("Pull Requests", u["pullRequests"]["totalCount"]),
    ("Issues", u["issues"]["totalCount"]),
    ("Public Repos", u["repositories"]["totalCount"]),
    ("Followers", u["followers"]["totalCount"]),
]
body = ""
for i, (label, value) in enumerate(rows):
    y = 70 + i * 22
    body += f'<circle cx="36" cy="{y - 4}" r="3.5" fill="{GOLD}"/>'
    body += f'<text x="50" y="{y}" font-family="{FONT}" font-size="14" fill="{TEXT}">{escape(label)}</text>'
    body += f'<text x="440" y="{y}" font-family="{FONT}" font-size="14" font-weight="600" fill="{TEXT}" text-anchor="end">{value}</text>'

# Languages card (bars grow in one after another)
lbody = ""
for i, (name, size) in enumerate(top):
    y = 68 + i * 24
    pct = size / total * 100
    bar = max(pct / 100 * 250, 3)
    opacity = 1 - i * 0.15
    lbody += f'<text x="30" y="{y + 4}" font-family="{FONT}" font-size="13" fill="{TEXT}">{escape(name)}</text>'
    lbody += f'<rect x="150" y="{y - 6}" width="250" height="10" rx="5" fill="#1C1C1C"/>'
    lbody += f'<rect x="150" y="{y - 6}" width="0" height="10" rx="5" fill="{GOLD}" opacity="{opacity:.2f}"><animate attributeName="width" from="0" to="{bar:.1f}" dur="1.2s" begin="{i * 0.15:.2f}s" fill="freeze"/></rect>'
    lbody += f'<text x="465" y="{y + 4}" font-family="{FONT}" font-size="12" fill="{MUTED}" text-anchor="end">{pct:.1f}%</text>'

os.makedirs("profile-cards", exist_ok=True)
open("profile-cards/stats.svg", "w", encoding="utf-8").write(frame("GitHub Stats", body))
open("profile-cards/languages.svg", "w", encoding="utf-8").write(frame("Most Used Languages", lbody))
print("done")
