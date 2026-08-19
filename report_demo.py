"""P3's day, in the console — the M48 checkpoint.

    python -m report_demo

Seeds a two-period day (plus a pre-M44 keyless record and a run from
YESTERDAY, both of which must stay off P3's sheet) and prints what
`class_report` makes of it. No server, no log file touched: this is the
data product talking, before any HTML exists to dress it up.
"""

from report import class_report

TODAY = "2026-08-19"
YESTERDAY = "2026-08-18"

# The catalog app.py will pass in for real (titles and right answers,
# handed over so report.py never has to import Flask).
CATALOG = {
    "challenges": {
        ("temp", "cold_store"): "The cold store",
        ("temp", "blast_freezer"): "The blast freezer",
        ("glucose", "t1_shift"): "The type 1 shift",
    },
    "cases": {
        ("temp", "case1"): {"title": "Case 1",
                            "answer_line": "the effector (shivering)"},
        ("temp", "case3"): {"title": "Case 3",
                            "answer_line": "the control center "
                                           "(hypothalamus)"},
    },
}


def _run(rid, team, period, when, loop, name, points, medal, met=True):
    return {"id": rid, "wall_time": when, "loop": loop, "mode": "challenge",
            "name": name, "label": team, "points": points, "medal": medal,
            "met": met, "rows": [], "period": period}


def _answer(rid, team, period, when, loop, name, correct):
    return {"id": rid, "wall_time": when, "loop": loop, "mode": "diagnosis",
            "name": name, "label": team, "points": 100 if correct else 0,
            "medal": None, "met": correct, "rows": [], "correct": correct,
            "answer": {"role": "control", "part": "hypothalamus"},
            "period": period}


LOG = [
    # P3, today — three teams, one of them stubborn.
    _run(1, "The Mongooses", "P3", f"{TODAY}T09:05:00", "temp",
         "cold_store", 88, "gold"),
    _run(2, "Team Kestrel", "P3", f"{TODAY}T09:07:00", "temp",
         "cold_store", 41, None),
    _run(3, "Team Kestrel", "P3", f"{TODAY}T09:19:00", "temp",
         "cold_store", 52, None),
    _run(4, "The Mongooses", "P3", f"{TODAY}T09:22:00", "temp",
         "blast_freezer", 30, None),
    _run(5, "Row 4", "P3", f"{TODAY}T09:24:00", "temp",
         "blast_freezer", 22, None, met=False),
    _answer(6, "The Mongooses", "P3", f"{TODAY}T09:31:00", "temp",
            "case1", True),
    _answer(7, "Team Kestrel", "P3", f"{TODAY}T09:33:00", "temp",
            "case1", False),
    _answer(8, "Row 4", "P3", f"{TODAY}T09:35:00", "temp", "case1", False),
    _answer(9, "Team Kestrel", "P3", f"{TODAY}T09:38:00", "temp",
            "case1", True),          # got there on the second try
    _answer(10, "The Mongooses", "P3", f"{TODAY}T09:41:00", "temp",
            "case3", True),
    # P5, today — a different class, must never appear on P3's sheet.
    _run(11, "Fifth Gear", "P5", f"{TODAY}T10:05:00", "glucose",
         "t1_shift", 95, "gold"),
    # P3, YESTERDAY — the date filter's job.
    _run(12, "Old News", "P3", f"{YESTERDAY}T09:05:00", "temp",
         "cold_store", 99, "gold"),
    # A pre-M44 record: no period key at all. Belongs to Unassigned.
    {"id": 13, "wall_time": f"{TODAY}T11:00:00", "loop": "temp",
     "mode": "challenge", "name": "cold_store", "label": "Before Periods",
     "points": 70, "medal": "silver", "met": True, "rows": []},
]


def _print_report(rep):
    head = f"{rep['period'] or 'Unassigned'} - {rep['date']}"
    print("=" * 64)
    print(head)
    print(f"{rep['team_count']} team(s), {rep['run_count']} finished run(s), "
          f"{rep['answer_count']} diagnosis answer(s)")
    print("=" * 64)
    if not rep["teams"]:
        print("  Nobody finished a run in this period on this date.")
        print()
        return
    for team in rep["teams"]:
        print(f"\n  {team['team']}")
        for row in team["challenges"]:
            medal = f" {row['best_medal'].upper()}" if row["best_medal"] else ""
            print(f"     {row['title']:<22} best {row['best_points']:>3}"
                  f"/100{medal}   ({row['runs']} run"
                  f"{'s' if row['runs'] != 1 else ''})")
        for row in team["cases"]:
            verdict = "right" if row["first_correct"] else "wrong"
            tail = ("" if row["first_correct"] or not row["ever_correct"]
                    else ", right on retry")
            print(f"     {row['title']:<22} first answer {verdict}{tail}")
    agg = rep["aggregate"]
    print("\n" + "-" * 64)
    print("  WHAT THE CLASS FOUND HARD")
    print("-" * 64)
    for row in agg["hardest_cases"]:
        line = (f"  {row['wrong']} of {row['teams']} teams got "
                f"{row['title']} wrong on their first answer")
        if row["answer_line"]:
            line += f" - it was {row['answer_line']}"
        print(line)
    for row in agg["medal_less"]:
        print(f"  No medal on {row['title']}: {row['teams']} team(s), "
              f"{row['runs']} run(s), best {row['best_points']}/100")
    print(f"  {agg['teams_reaching_a_case']} of {rep['team_count']} teams "
          "got as far as diagnosing a case")
    if agg["thin"]:
        print("  (few answers today - read the lines above as anecdotes, "
              "not as a class trend)")
    print()


def main():
    for period in ("P3", "P5", ""):
        _print_report(class_report(LOG, period, TODAY, CATALOG))
    print("The same log, P3, yesterday - the date filter at work:")
    _print_report(class_report(LOG, "P3", YESTERDAY, CATALOG))
    print("And a period nobody played today:")
    _print_report(class_report(LOG, "P7", TODAY, CATALOG))


if __name__ == "__main__":
    main()
