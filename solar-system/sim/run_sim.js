// run_sim.js
// runs the simulation without graphics and saves the results to csv files
// so they can be analyzed in python (analysis/analyze.py)
//
// usage: node sim/run_sim.js

var fs = require("fs");
var path = require("path");
var physics = require("../physics.js");

var DATA_DIR = path.join(__dirname, "..", "data");
fs.mkdirSync(DATA_DIR, { recursive: true });

// run one simulation and save time, energy, and every body's position/velocity
function runAndSave(method, dt, years, saveEvery, fileName) {
    var bodies = physics.createBodies();
    var steps = Math.round(years / dt);
    var stepsPerSave = Math.round(saveEvery / dt);

    var header = ["t", "energy"];
    for (var i = 0; i < bodies.length; i++) {
        var n = bodies[i].name;
        header.push(n + "_x", n + "_z", n + "_vx", n + "_vz");
    }
    var lines = [header.join(",")];

    function saveRow(t) {
        var row = [t, physics.totalEnergy(bodies)];
        for (var i = 0; i < bodies.length; i++) {
            var b = bodies[i];
            row.push(b.x, b.z, b.vx, b.vz);
        }
        lines.push(row.join(","));
    }

    saveRow(0);
    for (var s = 1; s <= steps; s++) {
        physics.step(bodies, dt, method);
        if (s % stepsPerSave === 0) saveRow(s * dt);
    }

    fs.writeFileSync(path.join(DATA_DIR, fileName), lines.join("\n") + "\n");
    console.log("saved " + fileName + " (" + steps + " steps)");
}

// 1. 200 years with each method, same starting conditions
runAndSave("verlet", 0.001, 200, 0.02, "verlet.csv");
runAndSave("euler", 0.001, 200, 0.02, "euler.csv");

// 2. timestep test: run 20 years with different dt values and record the
//    biggest energy error. a 1st order method's error should drop by 2x when
//    dt is halved, a 2nd order method's by 4x
var lines = ["method,dt,max_energy_error"];
var dts = [0.016, 0.008, 0.004, 0.002, 0.001, 0.0005];
var methods = ["euler", "verlet"];

for (var m = 0; m < methods.length; m++) {
    for (var d = 0; d < dts.length; d++) {
        var bodies = physics.createBodies();
        var startEnergy = physics.totalEnergy(bodies);
        var maxError = 0;
        var steps = Math.round(20 / dts[d]);

        for (var s = 0; s < steps; s++) {
            physics.step(bodies, dts[d], methods[m]);
            var error = Math.abs((physics.totalEnergy(bodies) - startEnergy) / startEnergy);
            maxError = Math.max(maxError, error);
        }
        lines.push(methods[m] + "," + dts[d] + "," + maxError);
    }
}
fs.writeFileSync(path.join(DATA_DIR, "timestep_test.csv"), lines.join("\n") + "\n");
console.log("saved timestep_test.csv");
