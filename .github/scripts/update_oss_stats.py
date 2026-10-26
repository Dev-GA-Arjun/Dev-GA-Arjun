
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date

OWNER = "Dev-GA-Arjun"
START = date.fromisoformat(os.environ["TRACKING_START_DATE"])
TOKEN = os.environ["GITHUB_TOKEN"]
API = "https://api.github.com"


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": "oss-profile-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def search_prs(query):
    results = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({
            "q": query,
            "per_page": 100,
            "page": page,
        })
        data = get_json(f"{API}/search/issues?{params}")
        results.extend(data["items"])
        if len(results) >= data["total_count"] or not data["items"]:
            break
    return results


start = START.isoformat()

opened = search_prs(
    f"author:{OWNER} type:pr created:>={start}"
)
merged = search_prs(
    f"author:{OWNER} type:pr is:merged merged:>={start}"
)
reviewed = search_prs(
    f"reviewed-by:{OWNER} type:pr updated:>={start}"
)

repositories = {
    pr["repository_url"]
    for pr in opened
    if pr.get("repository_url")
}

readme = open("README.md", encoding="utf-8").read()

stats = f"""<!-- OSS-STATS:START -->

| Metric | Progress |
|---|---:|
| Merged PRs | {len(merged)} / 100 |
| PRs opened | {len(opened)} |
| PRs reviewed | {len(reviewed)} |
| Repositories contributed to | {len(repositories)} |
| Active contribution days | Update pending |

<!-- OSS-STATS:END -->"""

updated, count = re.subn(
    r"<!-- OSS-STATS:START -->.*?<!-- OSS-STATS:END -->",
    lambda _: stats,
    readme,
    count=1,
    flags=re.S,
)

if count != 1:
    raise RuntimeError("README statistics markers were not found.")

with open("README.md", "w", encoding="utf-8", newline="\n") as file:
    file.write(updated)

print("Open-source statistics updated.")
