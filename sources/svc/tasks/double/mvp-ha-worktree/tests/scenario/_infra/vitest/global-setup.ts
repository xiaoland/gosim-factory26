import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { TestProject } from "vitest/node";
import {
  createScenarioDatabase,
  installScenarioDatabaseEnv,
  resetAndMigrateTestDatabase,
  type ScenarioDatabaseHandle,
} from "../../../../apps/backend/tests/_infra/db/test-database";
import { startBackendServer, type StartedBackendServer } from "../server/backend-server";
import { startFrontendServer, type StartedFrontendServer } from "../server/frontend-server";
import { getAvailablePort } from "../server/ports";
import { loadWorkspaceEnvFiles } from "../environment/env-files";
import {
  ensureDoubleScenarios,
  startScenarioDouble,
  stopRegisteredDoubles,
  type StartedScenarioDouble,
} from "../double/svc-double";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../..");

let backendServer: StartedBackendServer | null = null;
let database: ScenarioDatabaseHandle | null = null;
let caocaoDouble: StartedScenarioDouble | null = null;
let weChatPayDouble: StartedScenarioDouble | null = null;
let frontendServer: StartedFrontendServer | null = null;

export async function setup(project: TestProject): Promise<void> {
  loadWorkspaceEnvFiles(repoRoot);

  const backendPort = await getAvailablePort();
  const frontendPort = await getAvailablePort();
  const frontendBaseUrl = `http://127.0.0.1:${frontendPort}`;

  process.env.PORT = String(backendPort);
  process.env.FRONTEND_URL = frontendBaseUrl;
  process.env.PAYMENT_NOTIFY_BASE_URL = `http://127.0.0.1:${backendPort}`;
  process.env.VITE_BACKEND_PORT = String(backendPort);
  process.env.VITE_PORT = String(frontendPort);
  process.env.VITE_API_URL = frontendBaseUrl;

  stopRegisteredDoubles(repoRoot);
  ensureDoubleScenarios(repoRoot);
  const modules = path.join(repoRoot, ".dev-server", "svc-double-scenarios");
  caocaoDouble = startScenarioDouble({
    repoRoot,
    module: path.join(modules, "caocao-default-multi.double.yaml"),
    backendBaseUrl: `http://127.0.0.1:${backendPort}`,
  });
  weChatPayDouble = startScenarioDouble({
    repoRoot,
    module: path.join(modules, "wechatpay-bootstrap.double.yaml"),
    backendBaseUrl: `http://127.0.0.1:${backendPort}`,
  });
  const weChatPayFixture = JSON.parse(
    readFileSync(
      path.join(repoRoot, "tasks", "svc-double-acceptance", "fixtures", "wechatpay.json"),
      "utf8",
    ),
  ) as {
    appId: string;
    mchId: string;
    apiV3Key: string;
    merchantCertificate: {
      serialNo: string;
      privateKeyPem: string;
      certificatePem: string;
    };
  };

  database = await createScenarioDatabase();
  const databaseUrl = installScenarioDatabaseEnv(database.databaseUrl);

  await resetAndMigrateTestDatabase(databaseUrl);

  backendServer = await startBackendServer(backendPort);
  frontendServer = await startFrontendServer({
    backendPort,
    port: frontendPort,
  });

  project.provide("systemScenarioEnvironment", {
    backendBaseUrl: backendServer.origin,
    caocaoDouble: {
      clientId: "svc-double-caocao-client",
      origin: caocaoDouble.origin,
      signKey: "svc-double-caocao-sign-key",
      runId: caocaoDouble.runId,
      module: caocaoDouble.module,
    },
    weChatPayDouble: {
      apiV3Key: weChatPayFixture.apiV3Key,
      appId: weChatPayFixture.appId,
      mchId: weChatPayFixture.mchId,
      merchantCertificate: weChatPayFixture.merchantCertificate,
      origin: weChatPayDouble.origin,
      runId: weChatPayDouble.runId,
      module: weChatPayDouble.module,
    },
    frontendBaseUrl: frontendServer.origin,
  });
}

export async function teardown(): Promise<void> {
  let closeDbError: unknown;

  await frontendServer?.close();
  await backendServer?.close();
  stopRegisteredDoubles(repoRoot);
  frontendServer = null;
  backendServer = null;
  caocaoDouble = null;
  weChatPayDouble = null;

  try {
    const { closeDb } = await import("../../../../apps/backend/src/lib/db");
    await closeDb();
  } catch (error) {
    closeDbError = error;
  }

  await database?.cleanup();
  database = null;

  if (closeDbError) {
    throw closeDbError;
  }
}

declare module "vitest" {
  export interface ProvidedContext {
    systemScenarioEnvironment: {
      backendBaseUrl: string;
      caocaoDouble: {
        origin: string;
        clientId: string;
        signKey: string;
        runId: string;
        module: string;
      };
      weChatPayDouble: {
        origin: string;
        appId: string;
        mchId: string;
        apiV3Key: string;
        merchantCertificate: {
          serialNo: string;
          privateKeyPem: string;
          certificatePem: string;
        };
        runId: string;
        module: string;
      };
      frontendBaseUrl: string;
    };
  }
}
