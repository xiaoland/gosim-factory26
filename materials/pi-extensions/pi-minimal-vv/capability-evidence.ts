import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

// Capture the actual provider-facing capability surface, without request headers
// or conversation bodies. This observes normal requests; it never changes them.
export default function capabilityEvidence(pi: any) {
  const seen = new Set<string>();
  pi.on('before_provider_request', (event: any) => {
    const directory = process.env.PI_CAPABILITY_EVIDENCE_DIR;
    if (!directory) return;
    const payload = event.payload ?? {};
    const record = {
      model: payload.model,
      instructions: payload.instructions,
      system: (payload.messages ?? []).filter((message: any) =>
        message.role === 'system' || message.role === 'developer'),
      tools: payload.tools ?? [],
    };
    const encoded = JSON.stringify(record, null, 2);
    const digest = crypto.createHash('sha256').update(encoded).digest('hex');
    if (seen.has(digest)) return;
    fs.mkdirSync(directory, { recursive: true });
    fs.writeFileSync(path.join(directory, `${digest}.json`), encoded + '\n');
    fs.appendFileSync(path.join(directory, 'observations.jsonl'), JSON.stringify({
      at: new Date().toISOString(), pid: process.pid, model: payload.model, sha256: digest,
    }) + '\n');
    seen.add(digest);
  });
}
