"""The per-period class report — Phase 12's data product (kickoff SS5).

One pure function, `class_report(attempts, period, date, catalog=None)`,
turning the attempts log into "P3's day, on one sheet": a team scorecard
and a class debrief, as plain data. The printable page renders what this
returns and computes nothing itself, so a later gradebook export can
read the same function and never drift from the paper.

Three deliberate properties, because this is the record a teacher grades
from:

  * PURE. The log and the date arrive as arguments — no clock read, no
    file read, no Flask import. Only the route knows what "today" is,
    which is what makes the report testable with a crafted log.
  * NOTHING INVENTED. Every number here comes out of a stored attempt.
    Where the log cannot answer something, the report says so (see
    `thin`) instead of dressing two runs up as a class trend.
  * FINISHED WORK ONLY. Nothing in the app records attendance, so a team
    that joined and never completed a run leaves no trace. The page says
    that in words; this module simply never pretends otherwise.

The `catalog` is how titles and right answers get here without importing
app.py (which imports Flask). Shape:

    {"challenges": {(loop, name): "Cold store"},
     "cases":      {(loop, name): {"title": "Case 3",
                                   "answer_line": "the control center"}}}

Without one the report still works and carries the raw engine keys.
"""

TEAMLESS = "(no team)"          # matches the leaderboard's wording (M27)

# Below this many answers, a "the class found X hard" claim is one or two
# teams having a bad afternoon, not a pattern worth reteaching. M50's
# phrasing reads this flag rather than guessing.
THIN_SAMPLE = 3


def _team_of(att):
    return (att.get("label") or "").strip() or TEAMLESS


def attempts_for(attempts, period, date):
    """Every attempt from one class on one day, oldest first.

    `period` "" is the Unassigned pile — and a pre-M44 record, which has
    no period key at all, belongs to it (`.get(..., "")`, the M44 rule).
    """
    picked = [a for a in attempts
              if a.get("period", "") == period
              and (a.get("wall_time") or "")[:10] == date]
    return sorted(picked, key=lambda a: (a.get("wall_time") or "",
                                         a.get("id") or 0))


def _title(catalog, kind, loop, name, default=None):
    if not catalog:
        return default or name
    entry = catalog.get(kind, {}).get((loop, name))
    if entry is None:
        return default or name
    if isinstance(entry, dict):
        return entry.get("title") or default or name
    return entry


def _answer_line(catalog, loop, name):
    """What the right answer WAS, in words — the debrief names it, which
    is exactly why this page is not for projecting mid-case."""
    if not catalog:
        return None
    entry = catalog.get("cases", {}).get((loop, name))
    return entry.get("answer_line") if isinstance(entry, dict) else None


def _case_role(catalog, loop, name):
    """(role key, role label) for one case - WHICH BOX of the loop it was
    broken in (M54), or (None, None) without a catalog."""
    if not catalog:
        return None, None
    entry = catalog.get("cases", {}).get((loop, name))
    if not isinstance(entry, dict):
        return None, None
    return entry.get("role"), entry.get("role_label")


def _team_challenges(runs, catalog):
    """One row per challenge this team finished, best run first."""
    by_key = {}
    for a in runs:
        key = (a.get("loop"), a.get("name"))
        row = by_key.setdefault(key, {
            "loop": key[0], "name": key[1],
            "title": _title(catalog, "challenges", key[0], key[1]),
            "runs": 0, "best_points": None, "best_medal": None,
            "met": False,
        })
        row["runs"] += 1
        points = a.get("points") or 0
        if row["best_points"] is None or points > row["best_points"]:
            row["best_points"] = points
            row["best_medal"] = a.get("medal")
        row["met"] = row["met"] or bool(a.get("met"))
    return sorted(by_key.values(),
                  key=lambda r: (-(r["best_points"] or 0), r["title"]))


def _team_cases(answers, catalog):
    """One row per case this team answered.

    Both `first_correct` and `ever_correct` are kept: the first answer is
    the diagnosis the team actually committed to, and getting there on a
    second try is a different (also real) thing. Grading policy is the
    teacher's; the paper reports both rather than choosing for them.
    """
    by_key = {}
    for a in answers:
        key = (a.get("loop"), a.get("name"))
        row = by_key.get(key)
        if row is None:
            row = by_key[key] = {
                "loop": key[0], "name": key[1],
                "title": _title(catalog, "cases", key[0], key[1]),
                "answers": 0,
                "first_correct": bool(a.get("correct")),
                "ever_correct": False,
                "points": a.get("points"),
            }
        row["answers"] += 1
        row["ever_correct"] = row["ever_correct"] or bool(a.get("correct"))
        row["points"] = max(row["points"] or 0, a.get("points") or 0)
    return sorted(by_key.values(), key=lambda r: r["title"])


def _aggregate(day, teams, catalog):
    """The debrief half: what the CLASS found hard, from the same runs."""
    answers = [a for a in day if a.get("mode") == "diagnosis"]
    runs = [a for a in day if a.get("mode") == "challenge"]

    # Which case tripped the most teams — counted on FIRST answers only,
    # because a team's first commit is the diagnosis they believed.
    first_by = {}
    for a in answers:
        key = (_team_of(a), a.get("loop"), a.get("name"))
        first_by.setdefault(key, a)          # `day` is oldest first
    wrong = {}
    for (team, loop, name), a in first_by.items():
        row = wrong.setdefault((loop, name), {
            "loop": loop, "name": name,
            "title": _title(catalog, "cases", loop, name),
            "answer_line": _answer_line(catalog, loop, name),
            "teams": 0, "wrong": 0,
        })
        row["teams"] += 1
        if not a.get("correct"):
            row["wrong"] += 1
    hardest = sorted((r for r in wrong.values() if r["wrong"]),
                     key=lambda r: (-r["wrong"], -r["teams"], r["title"]))

    # M54: the same first answers, asked a different question - not
    # "which case was hard" but "which BOX of the loop can this class
    # not spot". A class that misses every effector case has a specific
    # gap, and it is not the same gap as missing every receptor case.
    by_role = {}
    for (team, loop, name), a in first_by.items():
        key, label = _case_role(catalog, loop, name)
        if key is None:
            continue                      # no catalog: nothing to say
        row = by_role.setdefault(key, {
            "role": key, "label": label, "answers": 0, "wrong": 0,
            "teams": set(), "cases": set(),
        })
        row["answers"] += 1
        row["teams"].add(team)
        row["cases"].add((loop, name))
        if not a.get("correct"):
            row["wrong"] += 1
    for row in by_role.values():
        row["teams"] = len(row["teams"])
        row["cases"] = len(row["cases"])
    hard_roles = sorted((r for r in by_role.values() if r["wrong"]),
                        key=lambda r: (-r["wrong"], -r["answers"],
                                       r["label"] or ""))

    # Challenges the class played and NOBODY medaled — the other half of
    # "what to reteach": not a wrong answer, a loop they could not hold.
    played = {}
    for a in runs:
        key = (a.get("loop"), a.get("name"))
        row = played.setdefault(key, {
            "loop": key[0], "name": key[1],
            "title": _title(catalog, "challenges", key[0], key[1]),
            "runs": 0, "teams": set(), "medals": 0, "best_points": 0,
        })
        row["runs"] += 1
        row["teams"].add(_team_of(a))
        if a.get("medal"):
            row["medals"] += 1
        row["best_points"] = max(row["best_points"], a.get("points") or 0)
    for row in played.values():
        row["teams"] = len(row["teams"])
    medal_less = sorted((r for r in played.values() if not r["medals"]),
                        key=lambda r: (-r["runs"], r["title"]))

    reached = sum(1 for t in teams if t["cases"])
    return {
        "hardest_cases": hardest,
        "hard_roles": hard_roles,
        "medal_less": medal_less,
        "challenges_played": sorted(played.values(),
                                    key=lambda r: (-r["runs"], r["title"])),
        "teams_reaching_a_case": reached,
        "answers": len(answers),
        # Loud about a small sample rather than confident about noise.
        "thin": len(answers) < THIN_SAMPLE,
    }


def assignment_progress(attempts, period, items, since=None,
                        catalog=None):
    """Did the reteach take? (M59)

    `items` are the assigned cases as (loop, name) dicts; `since` is the
    ISO stamp the assignment was set at, so "answered AFTER we talked
    about it" is answerable. Everything comes out of the attempts log -
    the one source of truth about who answered what - and nothing is
    tracked separately.

    Per case: how many teams have answered it since, and how many got it
    right. Per team: how many of the set they have finished. A team that
    answered a case BEFORE the assignment has not done the follow-up,
    which is why `since` is not optional in spirit even though the
    signature tolerates None.
    """
    wanted = {(i["loop"], i["name"]) for i in items}
    answers = [a for a in attempts
               if a.get("mode") == "diagnosis"
               and a.get("period", "") == period
               and (a.get("loop"), a.get("name")) in wanted
               and (since is None or (a.get("wall_time") or "") >= since)]
    # First answer per (team, case) since the assignment - a retry is
    # not a second team, the M50 rule.
    first = {}
    for a in sorted(answers, key=lambda a: (a.get("wall_time") or "",
                                            a.get("id") or 0)):
        first.setdefault((_team_of(a), a.get("loop"), a.get("name")), a)

    cases = []
    for item in items:
        key = (item["loop"], item["name"])
        mine = [a for (t, l, n), a in first.items() if (l, n) == key]
        cases.append({
            "loop": item["loop"], "name": item["name"],
            "n": item.get("n"),
            "title": _title(catalog, "cases", key[0], key[1]),
            "answers": len(mine),
            "correct": sum(1 for a in mine if a.get("correct")),
        })
    teams = {}
    for (team, loop, name), a in first.items():
        row = teams.setdefault(team, {"team": team, "done": 0,
                                      "correct": 0, "of": len(wanted)})
        row["done"] += 1
        if a.get("correct"):
            row["correct"] += 1
    total = sum(c["answers"] for c in cases)
    return {
        "cases": cases,
        "teams": sorted(teams.values(), key=lambda r: r["team"].lower()),
        "answers": total,
        "correct": sum(c["correct"] for c in cases),
        "of": len(wanted),
    }


# The gradebook's frozen column order (M55). Long format: one row per
# team per thing they did, so a team that played three challenges never
# produces ragged columns. Appended to, never reordered - a teacher's
# saved spreadsheet template reads these positions.
GRADEBOOK_FIELDS = ["period", "date", "team", "kind", "loop", "item",
                    "best_points", "medal", "attempts", "first_correct"]


def gradebook_rows(report):
    """One report -> the rows of its gradebook CSV (M55).

    A VIEW of `class_report()`, never a second computation: every value
    here was already on the printed sheet, so the spreadsheet and the
    paper can never disagree. Blank (not zero) where a column does not
    apply to that kind of row - an empty cell is honest, a 0 would be a
    score.
    """
    rows = []
    for team in report["teams"]:
        for row in team["challenges"]:
            rows.append({
                "period": report["period"], "date": report["date"],
                "team": team["team"], "kind": "challenge",
                "loop": row["loop"], "item": row["title"],
                "best_points": row["best_points"],
                "medal": row["medal"] if "medal" in row
                         else row["best_medal"] or "",
                "attempts": row["runs"], "first_correct": "",
            })
        for row in team["cases"]:
            rows.append({
                "period": report["period"], "date": report["date"],
                "team": team["team"], "kind": "case",
                "loop": row["loop"], "item": row["title"],
                "best_points": row["points"], "medal": "",
                "attempts": row["answers"],
                "first_correct": 1 if row["first_correct"] else 0,
            })
    return rows


def class_report(attempts, period, date, catalog=None):
    """One class period's day, as plain data.

    An empty day is a valid report, not an error: a period nobody played
    prints a page that says nobody played.
    """
    day = attempts_for(attempts, period, date)
    by_team = {}
    for a in day:
        by_team.setdefault(_team_of(a), []).append(a)

    teams = []
    for name, own in by_team.items():
        runs = [a for a in own if a.get("mode") == "challenge"]
        answers = [a for a in own if a.get("mode") == "diagnosis"]
        challenges = _team_challenges(runs, catalog)
        teams.append({
            "team": name,
            "challenges": challenges,
            "cases": _team_cases(answers, catalog),
            "runs": len(runs),
            "answers": len(answers),
            "best_points": max((c["best_points"] or 0
                                for c in challenges), default=None),
        })
    # Alphabetical, case-insensitive, with the unnamed team last — a
    # grading sheet is read by name, not by rank.
    teams.sort(key=lambda t: (t["team"] == TEAMLESS, t["team"].lower()))

    return {
        "period": period,
        "date": date,
        "teams": teams,
        "team_count": len(teams),
        "run_count": sum(t["runs"] for t in teams),
        "answer_count": sum(t["answers"] for t in teams),
        "aggregate": _aggregate(day, teams, catalog),
    }
