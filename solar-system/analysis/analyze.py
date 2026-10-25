"""
analyze.py - checks the simulation against real physics

reads the csv files from sim/run_sim.js and checks:
  1. kepler's third law: does each planet's measured orbital period match T = 2*pi*sqrt(a^3 / GM)?
  2. energy conservation: how much does the total energy drift with euler vs verlet?
  3. timestep test: how fast does the error shrink when dt gets smaller?

usage: python analysis/analyze.py   (run node sim/run_sim.js first)
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = "data"
OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)

G = 4 * np.pi**2  # AU^3 / (solar mass * year^2), same as physics.js

# planet masses in solar masses (same as PLANETS in physics.js)
MASSES = {"Mercury": 1.66e-7, "Venus": 2.45e-6, "Earth": 3.00e-6,
          "Mars": 3.23e-7, "Jupiter": 9.55e-4}

PLANET_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
VERLET_COLOR = "#2a78d6"
EULER_COLOR = "#eb6834"

results = []  # lines for results.txt


def report(line=""):
    print(line)
    results.append(line)


verlet = pd.read_csv(os.path.join(DATA_DIR, "verlet.csv"))
euler = pd.read_csv(os.path.join(DATA_DIR, "euler.csv"))


# ---------------------------------------------------------------------------
# 1. kepler's third law
# ---------------------------------------------------------------------------
def measure_orbit(df, name):
    """returns (semi-major axis, measured period) for one planet"""
    # position and velocity relative to the sun
    x = (df[name + "_x"] - df["Sun_x"]).values
    z = (df[name + "_z"] - df["Sun_z"]).values
    vx = (df[name + "_vx"] - df["Sun_vx"]).values
    vz = (df[name + "_vz"] - df["Sun_vz"]).values
    t = df["t"].values

    mu = G * (1 + MASSES[name])
    r = np.sqrt(x**2 + z**2)
    v2 = vx**2 + vz**2

    # semi-major axis from the vis-viva equation (v^2 = mu * (2/r - 1/a)),
    # averaged over the whole run
    a = np.mean(1 / (2 / r - v2 / mu))

    # period: find every time the planet crosses the +x axis going
    # counterclockwise (z goes from negative to positive), then average the
    # time between crossings. linear interpolation finds the exact crossing time
    i = np.where((z[:-1] < 0) & (z[1:] >= 0) & (x[:-1] > 0))[0]
    crossings = t[i] + (-z[i] / (z[i + 1] - z[i])) * (t[i + 1] - t[i])
    period = np.mean(np.diff(crossings))

    return a, period


report("=== Kepler's third law (Verlet, 200 years) ===")
report(f"{'planet':<9} {'a (AU)':>8} {'measured T':>11} {'Kepler T':>10} {'difference':>11}")

a_values, periods = [], []
for name in MASSES:
    a, period = measure_orbit(verlet, name)
    predicted = 2 * np.pi * np.sqrt(a**3 / (G * (1 + MASSES[name])))
    diff = 100 * (period - predicted) / predicted
    report(f"{name:<9} {a:8.4f} {period:10.4f}y {predicted:9.4f}y {diff:+10.4f}%")
    a_values.append(a)
    periods.append(period)

# on a log-log plot T vs a should be a straight line with slope 1.5 (T^2 = a^3)
slope, intercept = np.polyfit(np.log(a_values), np.log(periods), 1)
report(f"log-log slope of T vs a: {slope:.5f} (should be 1.5)")
report()

plt.figure(figsize=(7, 5))
a_line = np.linspace(1.5, 7.5, 50)
plt.loglog(a_line, a_line**1.5, "--", color="gray", label="Kepler: T = a^1.5")
plt.loglog(a_values, periods, "o", color=VERLET_COLOR, markersize=8, label="measured from simulation")
for name, a, period in zip(MASSES, a_values, periods):
    plt.annotate(name, (a, period), xytext=(-10, 8), textcoords="offset points", ha="right")
plt.minorticks_off()
plt.xticks([2, 3, 4, 5, 7], ["2", "3", "4", "5", "7"])
plt.yticks([2, 5, 10, 20], ["2", "5", "10", "20"])
plt.xlabel("semi-major axis a (AU)")
plt.ylabel("orbital period T (years)")
plt.title(f"Kepler's third law (fitted slope = {slope:.4f})")
plt.legend()
plt.grid(True, which="both", alpha=0.3)
plt.savefig(os.path.join(OUT_DIR, "kepler.png"), dpi=150, bbox_inches="tight")
plt.close()


# ---------------------------------------------------------------------------
# 2. energy conservation
# ---------------------------------------------------------------------------
def energy_error(df):
    E = df["energy"].values
    return np.abs((E - E[0]) / E[0])


report("=== Energy conservation (dt = 0.001 years, 200 years) ===")
report(f"Verlet max energy error: {energy_error(verlet).max():.2e}")
report(f"Euler  max energy error: {energy_error(euler).max():.2e}")

mercury_a_verlet, _ = measure_orbit(verlet.tail(500), "Mercury")
mercury_a_euler, _ = measure_orbit(euler.tail(500), "Mercury")
report(f"Mercury's orbit size at the end: Verlet {mercury_a_verlet:.3f} AU, "
       f"Euler {mercury_a_euler:.3f} AU (started at 1.700)")
report()

plt.figure(figsize=(8, 5))
t = verlet["t"]
plt.semilogy(t[1:], energy_error(verlet)[1:], color=VERLET_COLOR, label="Velocity Verlet")
plt.semilogy(t[1:], energy_error(euler)[1:], color=EULER_COLOR, label="Euler")
plt.xlabel("time (years)")
plt.ylabel("relative energy error |dE / E0|")
plt.title("Energy error over time (dt = 0.001 years)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUT_DIR, "energy.png"), dpi=150, bbox_inches="tight")
plt.close()

# orbits: all planets with verlet, and mercury with euler vs verlet
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
for name, color in zip(MASSES, PLANET_COLORS):
    axes[0].plot(verlet[name + "_x"], verlet[name + "_z"], lw=0.4, color=color, label=name)
axes[0].plot(0, 0, "o", color="black", markersize=8)
axes[0].set_title("All orbits over 200 years (Verlet)")
legend = axes[0].legend(loc="upper right", fontsize=8)
for line in legend.get_lines():
    line.set_linewidth(2)  # thin orbit lines are hard to see in the legend

axes[1].plot(euler["Mercury_x"] - euler["Sun_x"], euler["Mercury_z"] - euler["Sun_z"],
             lw=0.4, color=EULER_COLOR, label="Euler")
axes[1].plot(verlet["Mercury_x"] - verlet["Sun_x"], verlet["Mercury_z"] - verlet["Sun_z"],
             lw=1.0, color=VERLET_COLOR, label="Verlet")
axes[1].plot(0, 0, "o", color="black", markersize=8)
axes[1].set_title("Mercury over 200 years: Euler spirals out, Verlet stays put")
axes[1].legend(loc="upper right")

for ax in axes:
    ax.set_aspect("equal")
    ax.set_xlabel("x (AU)")
    ax.set_ylabel("z (AU)")
    ax.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUT_DIR, "orbits.png"), dpi=150, bbox_inches="tight")
plt.close()


# ---------------------------------------------------------------------------
# 3. timestep test
# ---------------------------------------------------------------------------
# if error ~ dt^p then log(error) vs log(dt) is a line with slope p (the order)
sweep = pd.read_csv(os.path.join(DATA_DIR, "timestep_test.csv"))

report("=== Timestep test (20 years) ===")
plt.figure(figsize=(7, 5))
for method, color, label in [("euler", EULER_COLOR, "Euler"), ("verlet", VERLET_COLOR, "Velocity Verlet")]:
    rows = sweep[sweep["method"] == method]
    order, _ = np.polyfit(np.log(rows["dt"]), np.log(rows["max_energy_error"]), 1)
    report(f"{label}: error shrinks like dt^{order:.2f}")
    plt.loglog(rows["dt"], rows["max_energy_error"], "o-", color=color,
               label=f"{label} (slope {order:.2f})")
plt.xlabel("timestep dt (years)")
plt.ylabel("max energy error over 20 years")
plt.title("Error vs timestep")
plt.legend()
plt.grid(True, which="both", alpha=0.3)
plt.savefig(os.path.join(OUT_DIR, "timestep.png"), dpi=150, bbox_inches="tight")
plt.close()

with open(os.path.join(OUT_DIR, "results.txt"), "w") as f:
    f.write("\n".join(results) + "\n")
print(f"\nsaved plots and results.txt to {OUT_DIR}/")
