import { inject } from "vitest";

export type SystemScenarioEnvironment = {
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

let currentEnvironment: SystemScenarioEnvironment | null = null;

export function installScenarioEnvironment(environment: SystemScenarioEnvironment): void {
  currentEnvironment = environment;
}

export function getScenarioEnvironment(): SystemScenarioEnvironment {
  if (!currentEnvironment) {
    return inject("systemScenarioEnvironment");
  }
  return currentEnvironment;
}

declare module "vitest" {
  export interface ProvidedContext {
    systemScenarioEnvironment: SystemScenarioEnvironment;
  }
}
