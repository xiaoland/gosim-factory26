export type Kind = 'issue' | 'pr';
export interface Selection { kind: Kind; id: number; agent?: string; provider?: string }
export interface ProviderSession {
  record_id: string;
  group_id?: string | null;
  work_item_kind?: Kind;
  work_item_id?: string;
  assignment_generation?: number | null;
  profile_id: string;
  provider: string;
  session_id?: string | null;
  native_session_id?: string | null;
  native_session_path?: string | null;
  parent_native_session_id?: string | null;
  status: string;
  context_revision?: string | null;
  effective_profile_digest?: string | null;
  context_path: string;
  instructions_path: string;
  worktree?: string | null;
  turns?: { braid_turn_id: string; provider_turn_id?: string | null; status: string; trigger_kind: string; input_path: string }[];
  source_mode?: 'archive';
  archive_native_error?: string | null;
}
export interface NativeEntry { offset: number; value?: Record<string, unknown>; error?: string; raw?: string }
export interface TranscriptPage { entries: NativeEntry[]; next_offset: number; size: number; eof: boolean; waiting: boolean }
export interface Run { id: string; label: string; writable: boolean; controllable: boolean; mode: 'live' | 'archive'; coverage: string[] }
export interface RuntimeState {
  status: string;
  running: boolean;
  paused: boolean;
  pid: number;
  started_at: string;
}
export interface ControlReceipt { runtime: RuntimeState; changed: boolean; writer_lock?: 'available' }
export interface Assignee { login: string }
export interface WorkItem {
  kind: Kind;
  id: number;
  number: number;
  title: string;
  state: string;
  assignees: Assignee[];
  revision: number;
}
export interface Relation {
  kind?: string;
  number: number;
  title: string;
  state?: string;
}
export interface Comment {
  database_id: string | number;
  author: Assignee;
  body: string | null;
  created_at: string;
  reply_to: number | null;
  thread_root: number;
  folded: boolean;
  resolved: boolean;
  minimized: boolean;
  minimized_reason: string | null;
  deleted: boolean;
  lifecycle: string;
}
export interface Item extends WorkItem {
  body: string;
  reason?: string | null;
  comments: Comment[];
  parent_issue?: Relation | null;
  sub_issues?: Relation[];
  associated_prs?: Relation[];
  associated_issues?: Relation[];
  headRefName?: string | null;
  baseRefName?: string | null;
  head_ref?: string | null;
  base_ref?: string | null;
  draft?: boolean;
}
export interface Action {
  action: 'edit' | 'comment' | 'hide' | 'unhide' | 'resolve' | 'unresolve' | 'close' | 'reopen';
  title?: string;
  body?: string;
  revision?: number;
  reply_to?: number | null;
  comment?: number;
  reason?: string;
}

export class ApiError extends Error {
  constructor(public status: number, detail: string) { super(`HTTP ${status}\n${detail}`); }
}

export async function api<T>(path: string, signal?: AbortSignal, payload?: object): Promise<T> {
  const response = await fetch(path, {
    cache: 'no-store', signal,
    ...(payload ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
  });
  const text = await response.text();
  let data: unknown;
  try { data = JSON.parse(text); }
  catch { throw new ApiError(response.status, text || '服务没有返回 JSON。'); }
  if (!response.ok) {
    const error = data as { error?: string; result?: string };
    throw new ApiError(response.status, [error.error || text, error.result].filter(Boolean).join('\n'));
  }
  return data as T;
}

export function url(path: string, params: Record<string, string | number>) {
  return `${path}?${new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)]))}`;
}
