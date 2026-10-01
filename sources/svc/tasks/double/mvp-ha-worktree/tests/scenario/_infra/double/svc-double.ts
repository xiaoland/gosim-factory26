import { execFileSync, spawnSync } from "node:child_process";
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

export type StartedScenarioDouble = {
  runId: string;
  origin: string;
  module: string;
};

export type DoubleObservation = {
  observation: {
    journal: {
      total: number;
      entries: Array<{
        kind: string;
        status: string;
        facts: Record<string, unknown>;
      }>;
    };
  };
};

const seed = "20260810";

const svcBin = (): string => process.env.SVC_DOUBLE_BIN?.trim() || "svc";

const runRegistry = (repoRoot: string): string =>
  path.join(repoRoot, ".dev-server", "svc-double-runs.jsonl");

const runSvc = <T>(repoRoot: string, args: string[]): T => {
  const completed = spawnSync(svcBin(), [...args, "--json"], {
    cwd: repoRoot,
    encoding: "utf8",
    env: process.env,
    maxBuffer: 4 * 1024 * 1024,
  });
  if (completed.error) throw completed.error;
  const stdout = completed.stdout.trim();
  if (stdout) return JSON.parse(stdout) as T;
  throw new Error(
    `svc ${args.join(" ")} failed with exit ${completed.status}: ${completed.stderr.trim()}`,
  );
};

export const ensureDoubleScenarios = (repoRoot: string): void => {
  const output = path.join(repoRoot, ".dev-server", "svc-double-scenarios");
  mkdirSync(output, { recursive: true });
  execFileSync(
    process.execPath,
    [
      path.join(repoRoot, "tasks", "svc-double-acceptance", "generate-scenarios.mjs"),
      output,
    ],
    { cwd: repoRoot, env: process.env, stdio: "inherit" },
  );
};

export const startScenarioDouble = (input: {
  repoRoot: string;
  module: string;
  backendBaseUrl: string;
}): StartedScenarioDouble => {
  const args = [
    "double",
    "start",
    input.module,
    "--seed",
    seed,
  ];
  if (/^\s*target:\s*consumer\.backend\s*$/m.test(readFileSync(input.module, "utf8"))) {
    args.push("--target", `consumer.backend=${input.backendBaseUrl}`);
  }
  const result = runSvc<{
    run_id: string;
    responder_url: string;
    module: string;
  }>(input.repoRoot, args);
  const registry = runRegistry(input.repoRoot);
  mkdirSync(path.dirname(registry), { recursive: true });
  appendFileSync(registry, `${JSON.stringify({ runId: result.run_id })}\n`, "utf8");
  return {
    runId: result.run_id,
    origin: result.responder_url,
    module: result.module,
  };
};

export const stopScenarioDouble = (repoRoot: string, runId: string): void => {
  runSvc(repoRoot, ["double", "stop", runId]);
  const registry = runRegistry(repoRoot);
  let raw: string;
  try {
    raw = readFileSync(registry, "utf8");
  } catch {
    return;
  }
  const retained = raw
    .split("\n")
    .filter(Boolean)
    .filter((line) => (JSON.parse(line) as { runId: string }).runId !== runId);
  writeFileSync(registry, retained.map((line) => `${line}\n`).join(""), "utf8");
};

export const emitScenarioDouble = (
  repoRoot: string,
  runId: string,
  event: string,
): void => {
  const result = runSvc<{ status: string; http_status: number | null }>(repoRoot, [
    "double",
    "emit",
    runId,
    event,
  ]);
  if (result.status !== "acknowledged") {
    throw new Error(
      `svc double event ${event} was not acknowledged: ${JSON.stringify(result)}`,
    );
  }
};

export const observeScenarioDouble = (
  repoRoot: string,
  runId: string,
): DoubleObservation => runSvc(repoRoot, ["double", "observe", runId]);

export const stopRegisteredDoubles = (repoRoot: string): void => {
  const registry = runRegistry(repoRoot);
  let raw: string;
  try {
    raw = readFileSync(registry, "utf8");
  } catch {
    return;
  }
  const runIds = new Set(
    raw
      .split("\n")
      .filter(Boolean)
      .map((line) => (JSON.parse(line) as { runId: string }).runId),
  );
  const remaining: string[] = [];
  for (const runId of runIds) {
    try {
      stopScenarioDouble(repoRoot, runId);
    } catch {
      remaining.push(runId);
    }
  }
  writeFileSync(
    registry,
    remaining.map((runId) => `${JSON.stringify({ runId })}\n`).join(""),
    "utf8",
  );
};

export const renderWeChatPayScenario = (
  repoRoot: string,
  providerInstanceId: string,
): string => {
  const directory = path.join(repoRoot, ".dev-server", "svc-double-scenarios");
  const template = readFileSync(path.join(directory, "wechatpay-bootstrap.double.yaml"), "utf8");
  const module = path.join(directory, `wechatpay-${providerInstanceId}.double.yaml`);
  writeFileSync(
    module,
    template.replaceAll("00000000-0000-4000-8000-000000000000", providerInstanceId),
    "utf8",
  );
  return module;
};
