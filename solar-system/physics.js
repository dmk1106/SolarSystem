// physics.js
// n-body gravity simulation. used by the webgl scene (solarsystem.js) and by
// the node script in sim/ that saves data for the python analysis.
//
// units: distance in AU, time in years, mass in solar masses (sun = 1).
// in these units G = 4*pi^2, which makes a planet at 1 AU take exactly
// 1 year to orbit, so kepler's third law becomes T^2 = a^3.
//
// everything moves in the x-z plane (y is "up" in the 3D scene).

"use strict";

var G = 4 * Math.PI * Math.PI;

// orbit sizes are squished so everything fits on screen, but the
// eccentricities and masses are the real values for each planet
var PLANETS = [
    //  name       a (AU)  ecc     mass (solar masses)  starting angle (deg)
    { name: "Mercury", a: 1.7, e: 0.206, mass: 1.66e-7, angle: 0   },
    { name: "Venus",   a: 2.5, e: 0.007, mass: 2.45e-6, angle: 70  },
    { name: "Earth",   a: 3.5, e: 0.017, mass: 3.00e-6, angle: 150 },
    { name: "Mars",    a: 5.0, e: 0.093, mass: 3.23e-7, angle: 230 },
    { name: "Jupiter", a: 7.0, e: 0.049, mass: 9.55e-4, angle: 300 }
];

function makeBody(name, mass, x, z, vx, vz) {
    return { name: name, mass: mass, x: x, z: z, vx: vx, vz: vz, ax: 0, az: 0 };
}

// builds the sun + planets at their starting positions
function createBodies() {
    var bodies = [makeBody("Sun", 1.0, 0, 0, 0, 0)];

    for (var i = 0; i < PLANETS.length; i++) {
        var p = PLANETS[i];

        // start each planet at its closest point to the sun (perihelion)
        var r = p.a * (1 - p.e);
        // vis-viva equation gives the orbital speed at distance r
        var speed = Math.sqrt(G * (1 + p.mass) * (2 / r - 1 / p.a));

        var angle = p.angle * Math.PI / 180;
        var x = r * Math.cos(angle);
        var z = r * Math.sin(angle);
        // at perihelion the velocity is perpendicular to the sun-planet line
        var vx = -speed * Math.sin(angle);
        var vz =  speed * Math.cos(angle);

        bodies.push(makeBody(p.name, p.mass, x, z, vx, vz));
    }

    // give the sun a small push the other way so total momentum is zero,
    // otherwise the whole system slowly drifts away
    var sun = bodies[0];
    for (var i = 1; i < bodies.length; i++) {
        sun.vx -= bodies[i].mass * bodies[i].vx / sun.mass;
        sun.vz -= bodies[i].mass * bodies[i].vz / sun.mass;
    }

    computeAccelerations(bodies); // verlet needs starting accelerations
    return bodies;
}

// gravity: every body pulls on every other body.
// a = G * m / dist^2 pointed toward the other body. (dx, dz) has length dist,
// so dividing it by dist^3 gives the right strength and direction.
function computeAccelerations(bodies) {
    for (var i = 0; i < bodies.length; i++) {
        bodies[i].ax = 0;
        bodies[i].az = 0;
    }

    for (var i = 0; i < bodies.length; i++) {
        for (var j = 0; j < bodies.length; j++) {
            if (i === j) continue;

            var dx = bodies[j].x - bodies[i].x;
            var dz = bodies[j].z - bodies[i].z;
            var dist = Math.sqrt(dx * dx + dz * dz);

            var strength = G * bodies[j].mass / (dist * dist * dist);
            bodies[i].ax += strength * dx;
            bodies[i].az += strength * dz;
        }
    }
}

// explicit euler: move with the current velocity, then update the velocity.
// simplest method, but it adds a little energy every step so orbits slowly
// spiral outward
function stepEuler(bodies, dt) {
    computeAccelerations(bodies);
    for (var i = 0; i < bodies.length; i++) {
        var b = bodies[i];
        b.x += b.vx * dt;
        b.z += b.vz * dt;
        b.vx += b.ax * dt;
        b.vz += b.az * dt;
    }
}

// velocity verlet: half a velocity update, a full position update, recompute
// gravity, then the other half of the velocity update. same cost as euler
// (one gravity calculation per step) but the energy stays stable long term
function stepVerlet(bodies, dt) {
    for (var i = 0; i < bodies.length; i++) {
        var b = bodies[i];
        b.vx += 0.5 * b.ax * dt;
        b.vz += 0.5 * b.az * dt;
        b.x += b.vx * dt;
        b.z += b.vz * dt;
    }

    computeAccelerations(bodies);

    for (var i = 0; i < bodies.length; i++) {
        var b = bodies[i];
        b.vx += 0.5 * b.ax * dt;
        b.vz += 0.5 * b.az * dt;
    }
}

function step(bodies, dt, method) {
    if (method === "euler") {
        stepEuler(bodies, dt);
    } else {
        stepVerlet(bodies, dt);
    }
}

// kinetic + potential energy of the whole system. this should stay constant,
// so how much it changes tells us how accurate the simulation is
function totalEnergy(bodies) {
    var kinetic = 0;
    var potential = 0;

    for (var i = 0; i < bodies.length; i++) {
        var b = bodies[i];
        kinetic += 0.5 * b.mass * (b.vx * b.vx + b.vz * b.vz);

        // count each pair once (j > i)
        for (var j = i + 1; j < bodies.length; j++) {
            var dx = bodies[j].x - b.x;
            var dz = bodies[j].z - b.z;
            potential -= G * b.mass * bodies[j].mass / Math.sqrt(dx * dx + dz * dz);
        }
    }
    return kinetic + potential;
}

// lets the node script in sim/ load this file too
if (typeof module !== "undefined") {
    module.exports = {
        G: G,
        PLANETS: PLANETS,
        createBodies: createBodies,
        step: step,
        totalEnergy: totalEnergy
    };
}
