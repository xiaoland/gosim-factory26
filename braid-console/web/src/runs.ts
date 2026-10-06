import { api } from './http';

export interface RunFacts {
  record: string | null;
  sha256?: string;
  variant?: string;
  experiment_name?: string;
  status?: string;
  updated_at?: string;
  error?: string;
}

// Permissions describe registration, not a promise that a later operation will succeed.
export interface RegisteredRun {
  id: string;
  label: string;
  harness: string;
  mode: 'live' | 'archive';
  writable: boolean;
  controllable: boolean;
  coverage: string[];
  read_check: 'saved-archive' | 'unavailable' | 'not-read';
  access_error: string | null;
  facts?: RunFacts;
  variant?: string;
  lifecycle?: string;
  activity?: string | null;
  as_of?: number | null;
}

export function registeredRuns(signal?: AbortSignal) {
  return api<RegisteredRun[]>('/api/runs', signal).then(rows => rows.map(row => ({
    ...row,
    facts: row.facts ?? { record: null, variant: row.variant, status: row.lifecycle,
      updated_at: row.as_of == null ? undefined : String(row.as_of) },
  })));
}

export function isBraidRun(run: RegisteredRun) {
  return `${run.variant ?? ''} ${run.harness ?? ''}`.toLowerCase().includes('braid');
}
