"""Fetch the real public GitHub contribution calendar, or explicit demo data."""
from __future__ import annotations

from datetime import date
import json
import os
import random
import urllib.error
import urllib.request

COLUMNS, ROWS = 53, 7
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch_calendar(login: str = "RaVSe", token: str | None = None) -> list[list[int]]:
    """Return levels[column][weekday], with Sunday at row 0.

    Never fall back silently to sample data: a token/API failure stops Actions.
    """
    token = token or os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing token. Set GITHUB_TOKEN or use --demo for sample data.")
    query = """query($login: String!) {
      user(login: $login) { contributionsCollection {
        contributionCalendar { weeks { contributionDays {
          date contributionCount contributionLevel
        } } }
      } }
    }"""
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        json.dumps({"query": query, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "RaVSe-Green-Mage-Calendar"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:350]
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to connect to GitHub API: {exc}") from exc
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {result['errors']}")
    user = (result.get("data") or {}).get("user")
    if user is None:
        raise RuntimeError(f"GitHub user not found: {login}")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    columns: list[list[int]] = []
    for week in weeks[-COLUMNS:]:
        col = [0] * ROWS
        for day in week["contributionDays"]:
            # GitHub weeks run Sun->Sat; do not confuse with Python Mon->Sun.
            weekday = (date.fromisoformat(day["date"]).weekday() + 1) % ROWS
            col[weekday] = LEVELS[day["contributionLevel"]]
        columns.append(col)
    return [[0] * ROWS for _ in range(max(0, COLUMNS - len(columns)))] + columns


def demo_calendar() -> list[list[int]]:
    """Illustrative data for offline preview only; not real GitHub activity."""
    rng = random.Random(75631)
    return [
        [rng.choices([0, 1, 2, 3, 4], weights=[56, 18, 13, 9, 4])[0]
         for _ in range(ROWS)]
        for _ in range(COLUMNS)
    ]
