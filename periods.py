"""Period codes (M43): the teacher's class list, from a text file.

`periods.txt` sits beside this file — one period name per line, `#`
comments and blank lines ignored, edited in Notepad once a year, read
once at launch. The whole feature keys off the list being non-empty:
a missing or empty file returns [] and joining is QUIETLY OFF — no
overlay, no badge, no error. The join step can never block the lesson.

Plain Python, no Flask: the parser is testable without a server, and
app.py just imports the list at startup.
"""

from pathlib import Path

PERIODS_FILE = Path(__file__).resolve().parent / "periods.txt"

# A projected join screen with a hundred buttons is a typo, not a
# schedule. Nobody teaches more periods than this in a day.
MAX_PERIODS = 12


def load_periods(path=PERIODS_FILE):
    """The period list, in the teacher's order, deduped.

    Missing file, unreadable file, or a file of nothing but comments all
    return [] — joining off, never an exception at launch.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        if name not in out:
            out.append(name)
    return out[:MAX_PERIODS]
