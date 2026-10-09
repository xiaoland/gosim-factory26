import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const digest = value => crypto.createHash('sha256').update(value).digest('hex');
const implementation = digest(fs.readFileSync(fileURLToPath(import.meta.url)));
function persist(file, value) {
  const temporary = `${file}.${crypto.randomUUID()}`;
  fs.writeFileSync(temporary, JSON.stringify(value, null, 2), { mode: 0o600 });
  fs.renameSync(temporary, file);
}
function fail(code, message) { throw Object.assign(new Error(message), { code }); }

// The execution owner supplies this non-secret recipe once. Caller shell state is not a recipe.
export async function execute(request, recipeFile = process.env.FACTORY26_E2E_RECIPE, signal) {
  const allowed = { open: ['operation', 'url', 'target'], discover: ['operation', 'handle', 'tool'],
    call: ['operation', 'handle', 'tool', 'args', 'saveImages'], close: ['operation', 'handle'] }[request.operation];
  if (!allowed || Object.keys(request).some(name => !allowed.includes(name)))
    fail('INVALID_REQUEST', 'Parameters do not belong to this operation; connection inputs are immutable');
  if (!recipeFile) fail('NO_RECIPE', 'The executor did not supply an owned E2E recipe');
  const recipe = JSON.parse(fs.readFileSync(recipeFile, 'utf8'));
  const root = fs.realpathSync(recipe.stateDirectory);
  const secret = process.env[recipe.credentialVariable];
  if (!secret || digest(secret) !== recipe.credentialFingerprint)
    fail('CONNECTION_CHANGED', 'The frozen E2E credential is missing or changed');
  if (request.operation === 'open') return open(request, recipe, root, secret, signal);
  if (['url', 'target', 'config', 'output', 'env'].some(name => request[name] !== undefined))
    fail('IMMUTABLE_RECIPE', 'Only open selects a target; live connection inputs cannot change');
  if (!/^[a-f0-9]{32}$/.test(request.handle ?? '')) fail('INVALID_HANDLE', 'An owned handle is required');
  const directory = path.join(root, request.handle);
  const file = path.join(directory, 'session.json');
  if (!fs.existsSync(file)) fail('UNKNOWN_HANDLE', 'No owned session has this handle');
  const lock = path.join(directory, 'operation.lock');
  try { fs.mkdirSync(lock); } catch (error) {
    if (error.code === 'EEXIST') fail('SESSION_BUSY', 'Another operation owns this handle');
    throw error;
  }
  try {
    const state = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (state.implementation !== implementation || state.recipeFingerprint !== digest(JSON.stringify(recipe)))
      fail('CONNECTION_CHANGED', 'This handle belongs to a different frozen client or recipe');
    if (state.status !== 'open' && !(request.operation === 'close' && state.session && ['open_failed', 'close_failed', 'open_unidentified'].includes(state.status)))
      fail('SESSION_ENDED', `Session state is ${state.status}; no automatic reopen`);
    let tool, args;
    if (request.operation === 'close') { tool = 'close_session'; args = { session: state.session }; }
    else if (request.operation === 'discover') { tool = 'tools'; args = { session: state.session, ...(request.tool ? { tool: request.tool } : {}) }; }
    else if (request.operation === 'call') {
      if (!request.tool) fail('INVALID_TOOL', 'call requires a catalog tool name');
      tool = 'call'; args = { session: state.session, tool: request.tool, args: request.args ?? {} };
    } else fail('INVALID_OPERATION', 'Use open, discover, call or close');
    const result = await invoke(recipe, state, secret, tool, args, request.saveImages, signal);
    if (result.isError && /NO_SESSION|kind['"]?\s*:\s*['"]offline/.test(result.stdout + result.stderr)) {
      state.status = 'lost'; persist(file, state); result.code = 'SESSION_LOST';
    } else if (request.operation === 'close') {
      state.status = result.isError ? 'close_failed' : /Cleanup:/.test(result.stdout) ? 'closed_cleanup_errors' : 'closed';
      result.cleanupFailed = state.status === 'closed_cleanup_errors';
      persist(file, state);
    }
    return { handle: request.handle, outputDirectory: state.output, ...result };
  } finally { fs.rmdirSync(lock); }
}

async function open(request, recipe, root, secret, signal) {
  if (!request.url) fail('INVALID_URL', 'open requires the owned application URL');
  const url = new URL(request.url);
  if (!['http:', 'https:'].includes(url.protocol)) fail('INVALID_URL', 'Use an HTTP application URL');
  if (request.config || request.output || request.env) fail('IMMUTABLE_RECIPE', 'Config, output and connection environment are executor-owned');
  const handle = crypto.randomUUID().replaceAll('-', '');
  const directory = path.join(root, handle);
  fs.mkdirSync(directory, { mode: 0o700 });
  const project = path.join(directory, 'project'); fs.mkdirSync(project);
  const config = path.join(project, 'e2e.config.ts'); fs.copyFileSync(recipe.configTemplate, config);
  fs.symlinkSync(recipe.nodeModules, path.join(project, 'node_modules'), 'dir');
  const state = { handle, session: null, status: 'opening', implementation,
    recipeFingerprint: digest(JSON.stringify(recipe)), project, config,
    configFingerprint: digest(fs.readFileSync(config)), url: url.href,
    output: path.join(project, 'output'), mcporterConfig: path.join(directory, 'mcporter.json') };
  fs.mkdirSync(state.output);
  persist(state.mcporterConfig, { imports: [], mcpServers: { e2e: {
    command: recipe.serverCommand, args: ['mcp', '--headless'], cwd: project, lifecycle: 'keep-alive' } } });
  state.mcporterFingerprint = digest(fs.readFileSync(state.mcporterConfig));
  persist(path.join(directory, 'session.json'), state);
  const result = await invoke(recipe, state, secret, 'open_session', { config, ...(request.target ? { target: request.target } : {}) }, undefined, signal);
  const session = /Session ([0-9a-f-]+)\b/.exec(result.stdout)?.[1];
  state.session = session ?? null;
  state.status = result.isError ? 'open_failed' : session ? 'open' : 'open_unidentified';
  persist(path.join(directory, 'session.json'), state);
  if (!session && !result.isError) { result.isError = true; result.code = 'INVALID_OPEN_RESULT'; }
  return { handle, outputDirectory: state.output, ...result };
}

async function invoke(recipe, state, secret, tool, args, saveImages, signal) {
  if (digest(fs.readFileSync(state.config)) !== state.configFingerprint)
    fail('CONNECTION_CHANGED', 'The owned config changed while its session was live');
  if (digest(fs.readFileSync(state.mcporterConfig)) !== state.mcporterFingerprint ||
      digest(fs.readFileSync(recipe.serverCommand)) !== recipe.serverFingerprint ||
      digest(fs.readFileSync(recipe.runtimeSource)) !== recipe.runtimeFingerprint)
    fail('CONNECTION_CHANGED', 'The frozen server configuration or runtime identity changed');
  const env = { ...recipe.environment, [recipe.credentialVariable]: secret,
    E2E_API_KEY: secret, E2E_CONFIG: state.config, E2E_APP_URL: state.url,
    E2E_OUTPUT_DIR: state.output, MCPORTER_CONFIG: state.mcporterConfig };
  const command = ['call', `e2e.${tool}`, '--args', JSON.stringify(args), '--output', 'raw'];
  if (saveImages || (tool === 'call' && args.tool === 'screenshot')) {
    const destination = path.resolve(saveImages ?? path.join(state.output, 'screenshots'));
    if (destination !== state.output && !destination.startsWith(state.output + path.sep))
      fail('INVALID_IMAGE_DESTINATION', 'Image output must belong to this attempt output directory');
    command.push('--save-images', destination);
  }
  const result = await new Promise(resolve => {
    const child = spawn(recipe.mcporterCommand, command, { env, cwd: state.project, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '', failure, termination;
    const abort = () => {
      if (termination) return;
      failure = 'Operation aborted; no automatic reopen';
      child.kill('SIGTERM');
      termination = setTimeout(() => child.kill('SIGKILL'), 5000);
    };
    child.stdout.setEncoding('utf8'); child.stderr.setEncoding('utf8');
    child.stdout.on('data', part => { stdout += part; if (stdout.length > 32 * 1024 * 1024) abort(); });
    child.stderr.on('data', part => { stderr += part; });
    child.on('error', error => { failure = error.message; });
    child.on('close', (exitCode, exitSignal) => {
      if (termination) clearTimeout(termination);
      signal?.removeEventListener('abort', abort);
      resolve({ isError: !!failure || exitCode !== 0, exitCode, exitSignal, stdout, stderr,
        ...(failure ? { error: failure, code: signal?.aborted ? 'ABORTED' : 'PROCESS_ERROR' } : {}) });
    });
    if (signal?.aborted) abort(); else signal?.addEventListener('abort', abort, { once: true });
  });
  // Full raw output stays in owned evidence, while image bytes never enter model context.
  const operation = crypto.randomUUID();
  const directory = path.dirname(state.project);
  fs.writeFileSync(path.join(directory, operation + '.stdout'), result.stdout, { mode: 0o600 });
  fs.writeFileSync(path.join(directory, operation + '.stderr'), result.stderr, { mode: 0o600 });
  result.stdoutEvidence = path.join(directory, operation + '.stdout');
  result.stderrEvidence = path.join(directory, operation + '.stderr');
  const bounded = text => text.replace(/(data:\s*['"])([A-Za-z0-9+/=]{256,})(['"])/g,
    (_match, lead, bytes, end) => `${lead}[image data: ${bytes.length} characters retained in evidence]${end}`).slice(0, 24000);
  result.stdoutTruncated = result.stdout.length > 24000; result.stderrTruncated = result.stderr.length > 24000;
  result.stdout = bounded(result.stdout); result.stderr = bounded(result.stderr);
  fs.appendFileSync(path.join(directory, 'operations.jsonl'), JSON.stringify({ at: new Date().toISOString(), tool, ...result }) + '\n', { mode: 0o600 });
  return result;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const cancellation = new AbortController();
  process.once('SIGTERM', () => cancellation.abort());
  process.once('SIGINT', () => cancellation.abort());
  try {
    const result = await execute(JSON.parse(process.argv[2]), undefined, cancellation.signal);
    console.log(JSON.stringify(result)); process.exitCode = result.isError ? 1 : 0;
  } catch (error) {
    console.error(JSON.stringify({ isError: true, code: error.code ?? 'CLIENT_ERROR', error: error.message })); process.exitCode = 1;
  }
}
