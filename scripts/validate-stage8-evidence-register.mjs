import fs from "node:fs";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const root = process.cwd();
const manifestRoot = path.join(root, "08-验收与案例");
const schemaPath = path.join(manifestRoot, "run-manifest.schema.json");
const schema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validateSchema = ajv.compile(schema);

function walk(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...walk(fullPath));
    else if (entry.isFile() && entry.name.toLowerCase().includes("manifest") && entry.name.endsWith(".json")) {
      files.push(fullPath);
    }
  }
  return files;
}

function repoFileExists(relativePath, sourceFile) {
  if (typeof relativePath !== "string" || relativePath.length === 0) {
    throw new Error(`${sourceFile}: artifact path must be a non-empty string`);
  }
  if (path.isAbsolute(relativePath) || relativePath.split(/[\\/]/).includes("..")) {
    throw new Error(`${sourceFile}: unsafe repository-relative artifact path: ${relativePath}`);
  }
  const resolved = path.resolve(root, relativePath);
  if (!resolved.startsWith(root + path.sep)) {
    throw new Error(`${sourceFile}: artifact path escapes repository: ${relativePath}`);
  }
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
    throw new Error(`${sourceFile}: referenced artifact does not exist in repository: ${relativePath}`);
  }
}

const manifests = [];
for (const file of walk(manifestRoot)) {
  const data = JSON.parse(fs.readFileSync(file, "utf8"));
  const relativeFile = path.relative(root, file).split(path.sep).join("/");
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error(`${relativeFile}: manifest must contain a JSON object`);
  }
  if (typeof data.run_id !== "string" || data.run_id.trim().length === 0) {
    throw new Error(`${relativeFile}: manifest is missing a non-empty run_id`);
  }
  manifests.push({ file, data });
}

if (manifests.length === 0) {
  throw new Error("No run manifest JSON files with run_id were found.");
}

const seenRunIds = new Map();
for (const { file, data } of manifests) {
  const relativeFile = path.relative(root, file).split(path.sep).join("/");
  if (!validateSchema(data)) {
    throw new Error(`${relativeFile}: schema validation failed:\n${JSON.stringify(validateSchema.errors, null, 2)}`);
  }

  if (seenRunIds.has(data.run_id)) {
    throw new Error(`Duplicate run_id "${data.run_id}" in ${seenRunIds.get(data.run_id)} and ${relativeFile}`);
  }
  seenRunIds.set(data.run_id, relativeFile);

  if (data.run_type === "case") {
    const match = /^S8-[0-9]{8}-(CASE-0[1-5])-[0-9]{3}$/.exec(data.run_id);
    if (!match || match[1] !== data.case_id) {
      throw new Error(`${relativeFile}: case_id must match the CASE segment in run_id`);
    }
    if (!Array.isArray(data.input_artifacts) || data.input_artifacts.length === 0) {
      throw new Error(`${relativeFile}: case manifest must include input_artifacts`);
    }
    for (const artifact of data.input_artifacts) {
      if (!/^[0-9a-f]{64}$/.test(artifact.sha256 ?? "") || !artifact.artifact_type) {
        throw new Error(`${relativeFile}: each case input artifact needs SHA-256 and artifact_type`);
      }
      if (artifact.availability === "tracked_in_main") repoFileExists(artifact.path, relativeFile);
    }
  }

  for (const artifact of data.artifacts ?? []) {
    repoFileExists(artifact.path, relativeFile);
  }

  console.log(`PASS: ${relativeFile} (${data.run_id}, ${data.status})`);
}

console.log(`All ${manifests.length} tracked run manifest(s) passed schema, identity, uniqueness and artifact-reference checks.`);
