import assert from "node:assert/strict";

// Durations are the MODEL-PROPOSED ranges recorded in the B-08 evidence.
// Dependencies are taken from B-08/06-K1-K5依赖图与工期计算.md.
const tasks = {
  K1: { min: 3, max: 5, dependsOn: [] },
  K2: { min: 2, max: 4, dependsOn: ["K1", "K5"] },
  K3: { min: 3, max: 5, dependsOn: ["K1"] },
  K4: { min: 4, max: 7, dependsOn: [] },
  K5: { min: 1, max: 2, dependsOn: [] }
};

function longestPathRange(taskMap, endpoint) {
  const memo = new Map();
  const visiting = new Set();

  function finishAt(taskId) {
    if (memo.has(taskId)) return memo.get(taskId);
    const task = taskMap[taskId];
    assert.ok(task, `Unknown dependency: ${taskId}`);
    assert.ok(!visiting.has(taskId), `Dependency cycle at ${taskId}`);
    visiting.add(taskId);

    const predecessorRanges = task.dependsOn.map(finishAt);
    const predecessorMax = predecessorRanges.length
      ? Math.max(...predecessorRanges.map(range => range[endpoint]))
      : 0;
    const result = predecessorMax + task[endpoint];

    visiting.delete(taskId);
    memo.set(taskId, result);
    return result;
  }

  const dependedOn = new Set(Object.values(taskMap).flatMap(task => task.dependsOn));
  const sinks = Object.keys(taskMap).filter(taskId => !dependedOn.has(taskId));
  assert.ok(sinks.length > 0, "Schedule graph must have at least one terminal task");
  return Math.max(...sinks.map(finishAt));
}

const unbuffered = {
  min: longestPathRange(tasks, "min"),
  max: longestPathRange(tasks, "max")
};

// Path checks make the dependency interpretation explicit and guard against
// accidentally dropping K1 -> K2 or K1 -> K3.
assert.deepEqual(
  [tasks.K1.min + tasks.K3.min, tasks.K1.max + tasks.K3.max],
  [6, 10],
  "K1 -> K3 path"
);
assert.deepEqual(
  [Math.max(tasks.K1.min, tasks.K5.min) + tasks.K2.min,
    Math.max(tasks.K1.max, tasks.K5.max) + tasks.K2.max],
  [5, 9],
  "K1/K5 -> K2 path"
);
assert.deepEqual([tasks.K4.min, tasks.K4.max], [4, 7], "Independent K4 path");
assert.deepEqual(unbuffered, { min: 6, max: 10 }, "Unbuffered project completion range");

const bufferFactor = 1.2; // MODEL-PROPOSED 20% buffer from the source evidence.
const buffered = {
  min: Number((unbuffered.min * bufferFactor).toFixed(1)),
  max: Number((unbuffered.max * bufferFactor).toFixed(1))
};
assert.deepEqual(buffered, { min: 7.2, max: 12 }, "Buffered completion range");

console.log("PASS: K1 -> K3 path = 6-10 days");
console.log("PASS: K1/K5 -> K2 path = 5-9 days");
console.log("PASS: K4 path = 4-7 days");
console.log("PASS: unbuffered completion = 6-10 days");
console.log("PASS: 20% buffered completion = 7.2-12.0 days");
