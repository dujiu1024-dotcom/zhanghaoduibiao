import fs from "node:fs";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const schemaPath = "08-验收与案例/run-manifest.schema.json";
const schema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validate = ajv.compile(schema);

const validPassed = {
  run_id: "S8-20261116-SYSTEM-001",
  stage: 8,
  run_type: "system",
  started_at: "2026-11-16T10:00:00Z",
  status: "passed",
  repository_commit: "a".repeat(40),
  environment: {
    trae_version: "Trae CN 3.4.20",
    model: null,
    workspace_trust: "trusted"
  },
  artifacts: [{
    path: "evidence/output.json",
    sha256: "b".repeat(64),
    artifact_type: "report"
  }],
  blockers: []
};

const validBlocked = {
  ...validPassed,
  run_id: "S8-20261116-SYSTEM-002",
  status: "completed_with_blockers",
  artifacts: [{ path: "evidence/legacy-index.json" }],
  blockers: ["A6.3 directory not registered"]
};

const validNotStarted = {
  ...validPassed,
  run_id: "S8-20261116-SYSTEM-003",
  started_at: null,
  status: "not_started",
  artifacts: []
};

const { blockers: _ignored, ...blockedWithoutBlockers } = validBlocked;
const cases = [
  ["valid passed manifest", validPassed, true],
  ["valid completed_with_blockers manifest with legacy path artifact", validBlocked, true],
  ["valid not_started template", validNotStarted, true],
  ["passed with no artifacts", { ...validPassed, artifacts: [] }, false],
  ["passed with artifact missing sha256", {
    ...validPassed,
    artifacts: [{ path: "evidence/output.json", artifact_type: "report" }]
  }, false],
  ["passed with blocker", {
    ...validPassed,
    blockers: ["unresolved"]
  }, false],
  ["completed_with_blockers without blockers", blockedWithoutBlockers, false],
  ["completed_with_blockers with empty blockers", {
    ...validBlocked,
    blockers: []
  }, false]
];

let failed = false;
for (const [name, data, expected] of cases) {
  const actual = validate(data);
  if (actual !== expected) {
    failed = true;
    console.error(`FAIL: ${name}; expected valid=${expected}`);
    if (!actual) console.error(validate.errors);
  } else {
    console.log(`PASS: ${name}`);
  }
}

if (failed) process.exit(1);
console.log(`All ${cases.length} Draft 2020-12 schema checks passed.`);
