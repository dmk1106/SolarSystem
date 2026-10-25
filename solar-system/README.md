# Solar System Simulation

A 3D solar system in WebGL where the planets are moved by a gravity simulation instead of fixed circular paths. Every body pulls on every other body (an n-body simulation), so the orbits come out as real ellipses. A Python script then checks the results against Kepler's laws and conservation of energy.

![orbits](results/orbits.png)

## Running it

Start a local server in the project folder, then open http://localhost:8000:

```
python -m http.server 8000
```

Controls:
- **W/S, A/D, Q/E**: move the camera, **drag**: look around, **scroll**: zoom
- **P**: pause
- **[ ]**: slow down / speed up the simulation
- **I**: switch between Velocity Verlet and Euler (restarts the sim)
- **R**: reset, **T**: toggle orbit trails, **H**: hide text

The top left shows the simulated time, the method, and how much the total energy has drifted. Switch to Euler and you can watch Mercury slowly spiral away from the sun.

## How the physics works

`physics.js` has all the simulation code.

- **Units:** AU for distance, years for time, solar masses for mass. With these units G = 4π², so a planet 1 AU from the sun takes exactly 1 year to orbit and Kepler's third law becomes T² = a³.
- **Gravity:** for every pair of bodies, a = G·m / dist², pointed toward the other body.
- **Starting positions:** each planet starts at its closest point to the sun, with its speed from the vis-viva equation, v² = GM(2/r − 1/a). The masses and eccentricities are the real values; the orbit sizes are squished so everything fits on screen.
- **Two ways to step forward in time:**
  - **Euler:** move with the current velocity, then update the velocity. Simple, but it adds a bit of energy every step, so orbits spiral outward.
  - **Velocity Verlet:** split the velocity update into two halves around the position update. It costs the same as Euler but keeps the energy stable.

## Checking it against real physics

```
node sim/run_sim.js          # runs the sim and saves csv files to data/
pip install -r requirements.txt
python analysis/analyze.py   # makes the plots and results.txt in results/
```

Results (from `results/results.txt`):
- **Kepler's third law:** each planet's measured period matches T = 2π√(a³/GM) to within 0.12%, and a log-log fit of period vs distance gives a slope of 1.50003 (theory: 1.5). Mars is the furthest off because Jupiter is close to it in this squished layout and pulls it around.
- **Energy:** over 200 simulated years, Verlet's energy error stays under 1×10⁻⁸. Euler's grows to 4.6%, and Mercury's orbit grows from 1.7 AU to 4.1 AU.
- **Timestep test:** halving the timestep cuts Euler's error in half (slope 0.92, about 1st order) and Verlet's by 4× (slope 2.00, 2nd order).

| ![energy](results/energy.png) | ![timestep](results/timestep.png) |
|---|---|

## Files

- `index.html`: page and shaders (including the procedural noise shader for the sun)
- `solarsystem.js`: WebGL rendering, camera, controls, orbit trails
- `physics.js`: the gravity simulation
- `sim/run_sim.js`: runs the simulation without graphics and saves data
- `analysis/analyze.py`: checks the data and makes the plots
- `MV.js`, `initShaders.js`: helper code from *Interactive Computer Graphics* (Angel & Shreiner); `webgl-utils.js`: from Google

Planet textures are loaded from the `mikiahk/webgl-solar-system` repo.
