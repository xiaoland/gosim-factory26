import { Type } from '@sinclair/typebox';
import { execute } from '../tools/owned-e2e.mjs';

export default function ownedE2E(pi: any) {
  pi.registerTool({
    name: 'e2e',
    label: 'Owned E2E session',
    description: 'Explore the current application without inner model calls. Only open accepts url/target. Retain its returned handle; later operations accept handle and cannot change connection inputs. Discover the actual catalog, call its tools (observe, locate, screenshot and actions), and close your own handle. Connection environment, configuration and output are owned by the executor; never use a raw mcporter E2E alias. Repeatable acceptance uses the TypeScript runner.',
    parameters: Type.Object({
      operation: Type.Union(['open', 'discover', 'call', 'close'].map(value => Type.Literal(value))),
      url: Type.Optional(Type.String()), target: Type.Optional(Type.String()),
      handle: Type.Optional(Type.String()), tool: Type.Optional(Type.String()),
      args: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      saveImages: Type.Optional(Type.String()),
    }),
    async execute(_id: string, parameters: any, signal: AbortSignal) {
      try {
        const result = await execute(parameters, undefined, signal);
        if (result.isError) throw Object.assign(new Error(JSON.stringify(result)), { ownedResult: result });
        return { content: [{ type: 'text', text: JSON.stringify(result) }], details: result };
      } catch (error: any) {
        const result = error.ownedResult ?? { isError: true, code: error.code ?? 'CLIENT_ERROR', error: error.message };
        // Pi marks thrown execution failures as tool errors, not successful results.
        throw new Error(JSON.stringify(result));
      }
    },
  });
}
