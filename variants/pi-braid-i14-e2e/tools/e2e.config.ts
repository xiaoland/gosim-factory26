import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';

const url = process.env.E2E_APP_URL;
if (!url) throw new Error('E2E_APP_URL must name the owned application service');

const provider = createOpenAICompatible({
  name: 'factory26',
  baseURL: process.env.FACTORY26_BASE_URL!,
  apiKey: process.env.FACTORY26_API_KEY,
});

export default {
  targets: [{ name: 'web', engine: web(), app: { url } }],
  workers: 1,
  retries: 0,
  trace: 'on',
  output: '.e2e',
  cache: 'off',
  agents: {
    default: {
      model: provider.chatModel('glm-5.3-flash'),
      providerOptions: { factory26: { reasoningEffort: 'high' } },
      maxModelCalls: 12,
      maxSteps: 12,
    },
  },
} satisfies E2EConfig;
