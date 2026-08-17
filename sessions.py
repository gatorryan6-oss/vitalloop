"""Per-browser sessions (M33): one set of Runners per student device.

The projector model (M7-M30) had exactly three Runners at module level.
Phase 9 keeps them — a client that presents no session id (verify.py,
pytest, curl, the teacher's old bookmarks) still drives those, so eight
phases of tests keep their meaning — and adds this registry: a browser
that presents a `vl_sid` cookie gets its OWN three loops, created on
first sight, swept after a long idle, and capped so a stray crowd can't
run the teacher's laptop out of memory mid-class.

The id is minted by the page's own JS (crypto.randomUUID) and lives in
a cookie; the server only ever reads it. App-level code, so reading the
clock is allowed (Runner.advance always has) — the engines below stay
deterministic. No Flask imports: the registry is plain Python behind
one lock, so the invariants suite can drive eviction and the cap with a
fake clock instead of sleeping.
"""

import threading
import time


class RoomFull(Exception):
    """A NEW session would push past the cap. Existing sessions are
    never evicted to make room — first come, first seated."""


class SessionRegistry:
    def __init__(self, factory, max_sessions, idle_s, clock=time.monotonic):
        self._factory = factory          # () -> fresh {loop: Runner}
        self.max_sessions = int(max_sessions)
        self.idle_s = float(idle_s)
        self._clock = clock
        self._lock = threading.Lock()
        self._sessions = {}              # sid -> {"runners", "last_seen"}

    def runners_for(self, sid):
        """This session's runners, created fresh on first sight.

        Touching a session keeps it alive; idle ones are swept on every
        access, so memory is bounded by the busiest period, not by the
        school day. An evicted (or never-seen) id is not an error — it
        gets a fresh healthy sandbox, which is also what makes a server
        restart harmless to the class: everyone quietly starts over.
        """
        now = self._clock()
        with self._lock:
            self._evict(now)
            entry = self._sessions.get(sid)
            if entry is None:
                if len(self._sessions) >= self.max_sessions:
                    raise RoomFull(
                        f"the room is full ({self.max_sessions} devices "
                        "are already playing) — close the app on a spare "
                        "tab or device, or ask the teacher to restart it")
                entry = {"runners": self._factory(), "last_seen": now}
                self._sessions[sid] = entry
            entry["last_seen"] = now
            return entry["runners"]

    def count(self):
        """Live sessions right now (the M34 footer reads this)."""
        with self._lock:
            self._evict(self._clock())
            return len(self._sessions)

    def _evict(self, now):
        # Callers hold self._lock.
        stale = [sid for sid, e in self._sessions.items()
                 if now - e["last_seen"] > self.idle_s]
        for sid in stale:
            del self._sessions[sid]
