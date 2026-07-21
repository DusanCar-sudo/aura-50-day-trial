import * as fs from "fs";
import * as os from "os";
import * as path from "path";

/**
 * Reads ~/.secrets/agents.env and loads it into process.env.
 * Skips comment lines (starting with #) and blank lines.
 * Never overrides existing environment variables.
 */
export function loadAgentsEnv(): void {
  const envPath = path.join(os.homedir(), ".secrets", "agents.env");

  if (!fs.existsSync(envPath)) {
    console.warn(`[loadAgentsEnv] File not found: ${envPath}`);
    return;
  }

  const content = fs.readFileSync(envPath, "utf-8");
  const lines = content.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = rawLine.trim();

    // Skip blank lines and comments
    if (line.length === 0 || line.startsWith("#")) {
      continue;
    }

    // Parse KEY=VALUE (allow = in value, split on first =)
    const eqIndex = line.indexOf("=");
    if (eqIndex === -1) {
      continue; // malformed line, skip
    }

    const key = line.slice(0, eqIndex).trim();
    let value = line.slice(eqIndex + 1).trim();

    // Strip surrounding quotes if present
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    // Never override existing env vars
    if (key in process.env) {
      continue;
    }

    process.env[key] = value;
  }
}
