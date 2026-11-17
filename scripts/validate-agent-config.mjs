import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const expectedAgents = [
  "competition-expert",
  "decision-challenger",
  "marketing-expert",
  "operations-expert",
  "research-expert",
  "strategy-expert"
];
const expectedSkills = [
  "business-diagnosis",
  "business-intake",
  "business-model-analysis",
  "commercial-decision-review",
  "customer-marketing-strategy",
  "execution-metrics-plan",
  "financial-unit-economics",
  "industry-competition-analysis",
  "performance-attribution-review",
  "strategic-planning"
];
const commonAgentTools = ["Read", "Grep", "Glob", "Write"];
const expectedAgentTools = {
  "research-expert": [...commonAgentTools, "WebSearch", "WebFetch"]
};
const errors = [];

function frontmatter(file) {
  const content = fs.readFileSync(file, "utf8");
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(content);
  if (!match) {
    errors.push(`${path.relative(root, file)}: missing YAML frontmatter`);
    return { content, fields: {} };
  }
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = /^([a-zA-Z_][\w-]*):\s*(.*)$/.exec(line);
    if (field) fields[field[1]] = field[2].trim();
  }
  return { content, fields };
}

function checkSet(kind, names) {
  const directory = path.join(root, ".trae", kind);
  const seen = new Set();
  for (const name of names) {
    const file = kind === "agents"
      ? path.join(directory, `${name}.md`)
      : path.join(directory, name, "SKILL.md");
    if (!fs.existsSync(file)) {
      errors.push(`missing expected ${kind} file: ${path.relative(root, file)}`);
      continue;
    }
    const { content, fields } = frontmatter(file);
    if (fields.name !== name) errors.push(`${path.relative(root, file)}: frontmatter name must equal ${name}`);
    if (!fields.description) errors.push(`${path.relative(root, file)}: missing description`);
    if (kind === "agents") {
      if (!fields.tools) errors.push(`${path.relative(root, file)}: missing tools`);
      else {
        const tools = fields.tools.split(",").map(value => value.trim()).filter(Boolean);
        const expected = expectedAgentTools[name] ?? commonAgentTools;
        if (tools.length !== expected.length || expected.some(tool => !tools.includes(tool))) {
          errors.push(`${path.relative(root, file)}: tools must be exactly ${expected.join(", ")}; found ${tools.join(", ")}`);
        }
      }
      if (!content.includes("## 统一交付门禁（强制）")) errors.push(`${path.relative(root, file)}: missing shared delivery gate`);
      if (!content.includes("## Write 工具边界（强制）")) errors.push(`${path.relative(root, file)}: missing Write boundary`);
      for (const required of ["work/cases/<case_id>/04-专家分析/", "禁止覆盖", "路径级 Write 沙箱"]) {
        if (!content.includes(required)) errors.push(`${path.relative(root, file)}: Write boundary missing ${required}`);
      }
      if (content.includes("accepted") && !content.includes("专家不得设置 `accepted`")) {
        errors.push(`${path.relative(root, file)}: accepted-state boundary is not explicit`);
      }
    }
    seen.add(fields.name);
    console.log(`PASS: ${path.relative(root, file)}`);
  }
  if (seen.size !== names.length) errors.push(`${kind}: expected ${names.length} unique named entries, found ${seen.size}`);
}

checkSet("agents", expectedAgents);
checkSet("skills", expectedSkills);

function extractSection(content, startHeading, endHeading) {
  const start = content.indexOf(startHeading);
  if (start < 0) return "";
  const bodyStart = start + startHeading.length;
  const end = content.indexOf(endHeading, bodyStart);
  return end < 0 ? content.slice(bodyStart) : content.slice(bodyStart, end);
}

function checkRoutingTable(section, expectedNames, label) {
  if (!section) {
    errors.push(`routing document missing ${label} table section`);
    return;
  }
  const names = section.split(/\\r?\\n/)
    .map(line => /^\\|\\s*([a-z][a-z0-9-]*)\\s*\\|/.exec(line)?.[1])
    .filter(Boolean);
  for (const name of expectedNames) {
    const count = names.filter(value => value === name).length;
    if (count !== 1) errors.push(`${label} routing table must contain exactly one row for ${name}; found ${count}`);
  }
  for (const name of names) {
    if (!expectedNames.includes(name)) errors.push(`${label} routing table contains unexpected entry: ${name}`);
  }
  if (names.length !== expectedNames.length) {
    errors.push(`${label} routing table expected ${expectedNames.length} entries, found ${names.length}`);
  }
}

const routingPath = path.join(root, "07-操盘手系统设计/Skill触发与路由边界.md");
const agentsPath = path.join(root, "AGENTS.md");
if (!fs.existsSync(routingPath)) errors.push("missing Skill routing boundary document");
else {
  const routing = fs.readFileSync(routingPath, "utf8");
  const skillSection = extractSection(routing, "## 2. 十个 Skill 的主责与排除边界", "## 3. 常见重叠的裁决规则");
  const agentSection = extractSection(routing, "## 4. Subagent 路由映射", "## 5. 调用与交付门禁");
  checkRoutingTable(skillSection, expectedSkills, "Skill");
  checkRoutingTable(agentSection, expectedAgents, "Subagent");
}
if (!fs.existsSync(agentsPath) || !fs.readFileSync(agentsPath, "utf8").includes("Skill触发与路由边界.md")) {
  errors.push("AGENTS.md must link the Skill routing boundary document");
}
if (errors.length) {
  for (const error of errors) console.error(`FAIL: ${error}`);
  process.exit(1);
}
console.log(`All ${expectedAgents.length} Subagents, ${expectedSkills.length} Skills and routing references passed static checks.`);
