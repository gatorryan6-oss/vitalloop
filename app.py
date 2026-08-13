"""Vital Loop — the Flask app. Routes and the sim runner; no physiology here.

The engine ticks LAZILY: every /state poll measures wall time since the last
poll, multiplies by the speed setting, and steps the sim that many 1 s ticks.
The engine never reads the clock, so it stays deterministic; the app only
decides HOW MANY ticks to run. No background thread to wedge mid-class.

If the tab is hidden for a while (polls stop), catch-up is capped at
MAX_CATCHUP_TICKS and the rest of the wall time is dropped — the sim resumes
smoothly instead of freezing the server chewing through an hour of ticks.
"""

import threading
import time

from flask import Flask, jsonify, render_template, request

from engine.sim import Simulation

app = Flask(__name__)

MAX_CATCHUP_TICKS = 2000     # ~2 sim-minutes at 16x; beyond that, drop time
MAX_POINTS_PER_RESPONSE = 1500   # downsample /state payloads beyond this


class Runner:
    """The single shared simulation and its play/pause/speed state."""

    def __init__(self):
        self.lock = threading.Lock()
        self.sim = Simulation()
        self.running = True
        self.speed = 1
        self._last_wall = time.monotonic()
        self._tick_debt = 0.0    # fractional ticks owed, carried between polls

    def advance(self):
        """Step the sim by however much wall time has passed (times speed)."""
        now = time.monotonic()
        with self.lock:
            elapsed = now - self._last_wall
            self._last_wall = now
            if not self.running:
                self._tick_debt = 0.0
                return
            self._tick_debt += elapsed * self.speed
            n = int(self._tick_debt)
            if n > MAX_CATCHUP_TICKS:
                n, self._tick_debt = MAX_CATCHUP_TICKS, 0.0
            else:
                self._tick_debt -= n
            if n:
                self.sim.step(n)

    def snapshot(self, since):
        """Current state + history records newer than sim-time `since`."""
        with self.lock:
            records = self.sim.history()
            state = records[-1]
        points = [r for r in records if r["t"] > since]
        if len(points) > MAX_POINTS_PER_RESPONSE:
            stride = -(-len(points) // MAX_POINTS_PER_RESPONSE)  # ceil div
            # Keep the newest point exact so the readout matches the chart.
            points = points[::stride] + [points[-1]]
        return {
            "running": self.running,
            "speed": self.speed,
            "now": state,
            "points": points,
        }


runner = Runner()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/state")
def state():
    runner.advance()
    since = request.args.get("since", -1.0, type=float)
    return jsonify(runner.snapshot(since))


@app.route("/control", methods=["POST"])
def control():
    """Play/pause/reset/speed. Disturbances and toggles arrive at M3/M5."""
    cmd = request.get_json(force=True, silent=True) or {}
    action = cmd.get("action")
    runner.advance()   # settle time owed under the OLD settings first
    with runner.lock:
        if action == "pause":
            runner.running = False
        elif action == "resume":
            runner.running = True
        elif action == "reset":
            runner.sim.reset()
            runner.running = True
        elif action == "speed":
            value = cmd.get("value")
            if value not in (1, 4, 16):
                return jsonify({"error": f"speed must be 1, 4 or 16, "
                                         f"got {value!r}"}), 400
            runner.speed = value
        else:
            return jsonify({"error": f"unknown action {action!r}"}), 400
    return jsonify(runner.snapshot(since=float("inf")))


if __name__ == "__main__":
    # run.bat lands here. Port is this project's own — see CLAUDE.md.
    app.run(port=5083)
