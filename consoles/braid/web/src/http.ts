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
