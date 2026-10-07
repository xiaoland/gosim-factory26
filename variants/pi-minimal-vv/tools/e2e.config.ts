import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';

const url = process.env.E2E_APP_URL;
if (!url) throw new Error('E2E_APP_URL must name the owned application service');

const baseURL = process.env.E2E_BASE_URL?.trim().replace(/\/+$/, '');
if (!baseURL) throw new Error('E2E_BASE_URL must name the selected model API');
if (!process.env.E2E_API_KEY) throw new Error('E2E_API_KEY must provide the selected model API key');
const model = process.env.E2E_MODEL;
if (!model) throw new Error('E2E_MODEL must name the selected wire model');

const provider = createOpenAICompatible({
  name: 'factory26',
  baseURL,
  apiKey: process.env.E2E_API_KEY,
});

export default {
  targets: [{ name: 'web', engine: web(), app: { url } }],
  workers: 1,
  retries: 0,
  trace: 'on',
  output: process.env.E2E_OUTPUT_DIR || '.e2e',
  cache: 'off',
  agents: {
    default: {
      model: provider.chatModel(model),
      providerOptions: { factory26: { reasoningEffort: 'high' } },
      maxModelCalls: 12,
      maxSteps: 12,
    },
  },
} satisfies E2EConfig;
