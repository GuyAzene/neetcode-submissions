"""Record NeetCode submissions in the LeetCode plan in Notion.

NeetCode pushes every solution to this repository as <topic>/<problem>/submission-<n>.<ext>.
A GitHub Action runs this file after each push. It finds the day of the newest submission of
every problem, reads the plan's rows from Notion and sets Status and Last attempt on the rows
that have something new:

  To do            ->  Solved
  Redo in 1 day    ->  Redo in 1 week    when the redo came a day or more after the last attempt
  Redo in 1 week   ->  Redo in 3 weeks   a week or more after
  Redo in 3 weeks  ->  Solved            three weeks or more after
  Solved           ->  Solved            only the date moves

A row is matched by the problem's name in its Link, neetcode.io/problems/<problem>. This file
cannot know whether a solution needed help, so that part stays by hand: set the row to
"Redo in 1 day" in Notion. It never moves a row back, it leaves a redo that came before it
was due alone, and it writes nothing but those two fields.

Solutions pushed up to START, below, do not count. They are old ones that NeetCode's bulk
sync brought in on 2026-11-16, solved before the plan began.

NeetCode has to be set to sync accepted solutions only (neetcode.io/profile/github), because
a pushed file does not say whether it passed. The access token is in NOTION_TOKEN.

  python3 .github/scripts/notion_sync.py             record what is new
  python3 .github/scripts/notion_sync.py --dry-run   say what would be recorded, change nothing
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
PLAN = "41afb956-622b-81ea-a997-000b22b488c6"  # the "LeetCode plan" database's data source
HOME = ZoneInfo("Asia/Jerusalem")  # a submission's day is the day it was in Israel
# The plan begins after this moment, the bulk sync of the old solutions.
START = datetime.fromisoformat("2026-11-16T08:07:02+00:00")

# How long each redo waits, in days, and where a row goes from each status.
WAIT = {"Redo in 1 day": 1, "Redo in 1 week": 7, "Redo in 3 weeks": 21}
NEXT = {
    "To do": "Solved",
    "Redo in 1 day": "Redo in 1 week",
    "Redo in 1 week": "Redo in 3 weeks",
    "Redo in 3 weeks": "Solved",
}

SUBMISSION = re.compile(r"^[^/]+/([^/]+)/submission-\d+\.\w+$")
PROBLEM_LINK = re.compile(r"neetcode\.io/problems/([^/?#]+)")


# The rule.


def decide(status, last, done):
    """The fields a row should get, given the day of the problem's newest submission.
    Empty when nothing is new."""
    if done is None or (last and done <= last):
        return {}
    if status in WAIT:
        if last is None:  # marked for a redo before this file saw the first attempt
            return {"Last attempt": done}
        if done < last + timedelta(days=WAIT[status]):
            return {}  # redone before it was due: the wait is not over
        return {"Status": NEXT[status], "Last attempt": done}
    if status == "To do":
        return {"Status": NEXT[status], "Last attempt": done}
    return {"Last attempt": done}


# The repository.


def submitted(repo="."):
    """The day of the newest submission of each problem since the plan began, from the
    history of the repository. Removing a file is not a submission."""
    log = subprocess.run(
        ["git", "-C", repo, "-c", "core.quotepath=off", "log", "--diff-filter=AM"]
        + ["--format=commit %cI", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    days, day = {}, None
    for line in log.splitlines():
        if line.startswith("commit "):
            moment = datetime.fromisoformat(line[len("commit ") :])
            day = moment.astimezone(HOME).date() if moment > START else None
            continue
        match = SUBMISSION.match(line)
        if match and day:
            problem = match.group(1)
            days[problem] = max(day, days.get(problem, day))
    return days


# Notion.


def call(method, path, body=None):
    """One request to Notion's API. Stops with Notion's own message when it refuses."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit("No NOTION_TOKEN is set. Add it to this repository's Actions secrets.")
    request = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        sys.exit(f"Notion refused ({error.code}): {detail[:300]}")


def rows():
    """Every row of the plan, as plain fields."""
    found, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        reply = call("POST", f"/data_sources/{PLAN}/query", body)
        found += [row_of(page) for page in reply.get("results", [])]
        cursor = reply.get("next_cursor")
        if not reply.get("has_more") or not cursor:
            return found


def row_of(page):
    """One Notion page as a plain dict."""
    fields = page.get("properties", {})
    title = fields.get("Problem", {}).get("title") or []
    link = fields.get("Link", {}).get("url") or ""
    day = (fields.get("Last attempt", {}).get("date") or {}).get("start") or ""
    return {
        "id": page["id"],
        "problem": "".join(piece.get("plain_text", "") for piece in title),
        "name": problem_in(link),
        "status": (fields.get("Status", {}).get("status") or {}).get("name", "To do"),
        "last": date.fromisoformat(day[:10]) if day else None,
    }


def problem_in(link):
    """NeetCode's name for a problem, from the address of its page; empty for another site."""
    match = PROBLEM_LINK.search(link or "")
    return match.group(1) if match else ""


def write(page_id, fields):
    shaped = {}
    if "Status" in fields:
        shaped["Status"] = {"status": {"name": fields["Status"]}}
    if "Last attempt" in fields:
        shaped["Last attempt"] = {"date": {"start": fields["Last attempt"].isoformat()}}
    call("PATCH", f"/pages/{page_id}", {"properties": shaped})


# The command.


def sync(days, dry_run=False):
    """Bring the plan up to date with the submissions. Returns the lines to print."""
    lines, known = [], set()
    for row in rows():
        if not row["name"]:
            continue
        known.add(row["name"])
        fields = decide(row["status"], row["last"], days.get(row["name"]))
        if not fields:
            continue
        if not dry_run:
            write(row["id"], fields)
        lines.append(described(row, fields))
    for problem in sorted(set(days) - known):
        lines.append(f"{problem}: not in the plan, left alone")
    return lines


def described(row, fields):
    status = fields.get("Status")
    change = f"{row['status']} -> {status}" if status else f"stays {row['status']}"
    return f"{row['problem']}: {change}, last attempt {fields['Last attempt'].isoformat()}"


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    days = submitted()
    lines = sync(days, dry_run)
    print(f"{len(days)} problems have submissions since the plan began.")
    for line in lines:
        print(("Would record: " if dry_run else "") + line)
    if not lines:
        print("Nothing new for the plan.")


if __name__ == "__main__":
    main()
