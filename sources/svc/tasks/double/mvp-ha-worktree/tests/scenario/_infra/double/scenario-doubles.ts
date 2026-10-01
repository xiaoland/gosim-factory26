import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  emitScenarioDouble,
  observeScenarioDouble,
  renderWeChatPayScenario,
  startScenarioDouble,
  stopScenarioDouble,
  type StartedScenarioDouble,
} from "./svc-double";
import {
  getScenarioEnvironment,
  installScenarioEnvironment,
} from "../environment/scenario-environment";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../..");

export type CaocaoDoubleVariant =
  | "default-multi"
  | "default-single"
  | "cancel-zero"
  | "create-failure"
  | "unavailable-5"
  | "unavailable-all";

const replaceHandle = async (
  kind: "caocao" | "wechatpay",
  module: string,
): Promise<StartedScenarioDouble> => {
  const current = getScenarioEnvironment();
  const previous = kind === "caocao" ? current.caocaoDouble : current.weChatPayDouble;
  stopScenarioDouble(repoRoot, previous.runId);
  const next = startScenarioDouble({
    repoRoot,
    module,
    backendBaseUrl: current.backendBaseUrl,
  });
  installScenarioEnvironment(
    kind === "caocao"
      ? {
          ...current,
          caocaoDouble: { ...current.caocaoDouble, ...next },
        }
      : {
          ...current,
          weChatPayDouble: { ...current.weChatPayDouble, ...next },
        },
  );
  return next;
};

export const useCaocaoDouble = (variant: CaocaoDoubleVariant): Promise<StartedScenarioDouble> =>
  replaceHandle(
    "caocao",
    path.join(repoRoot, ".dev-server", "svc-double-scenarios", `caocao-${variant}.double.yaml`),
  );

export const useWeChatPayDouble = (
  providerInstanceId: string,
): Promise<StartedScenarioDouble> =>
  replaceHandle("wechatpay", renderWeChatPayScenario(repoRoot, providerInstanceId));

export const emitCaocaoEvent = (event: string): void => {
  const environment = getScenarioEnvironment();
  emitScenarioDouble(repoRoot, environment.caocaoDouble.runId, event);
};

export const emitWeChatPaySucceeded = (): void => {
  const environment = getScenarioEnvironment();
  emitScenarioDouble(repoRoot, environment.weChatPayDouble.runId, "payment.succeeded");
};

export const matchedInteractionCount = (
  kind: "caocao" | "wechatpay",
  interaction?: string,
): number => {
  const environment = getScenarioEnvironment();
  const handle = kind === "caocao" ? environment.caocaoDouble : environment.weChatPayDouble;
  const observation = observeScenarioDouble(repoRoot, handle.runId);
  return observation.observation.journal.entries.filter(
    (entry) =>
      entry.kind === "request" &&
      entry.status === "matched" &&
      (interaction === undefined || entry.facts.interaction === interaction),
  ).length;
};

export const doubleJournalTotal = (kind: "caocao" | "wechatpay"): number => {
  const environment = getScenarioEnvironment();
  const handle = kind === "caocao" ? environment.caocaoDouble : environment.weChatPayDouble;
  return observeScenarioDouble(repoRoot, handle.runId).observation.journal.total;
};
