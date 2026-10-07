import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from './http';
import { isBraidRun, type RegisteredRun } from './runs';

type Props = { runId: string; currentRun: RegisteredRun };
type Row = Record<string, unknown>;
const text = (value: unknown) => value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value);
const timestamp = (value: unknown) => typeof value === 'number' ? new Date(value * 1000).toLocaleString(undefined, { timeZoneName: 'short' }) : text(value);

function Table({ rows, fields }: { rows: unknown[]; fields: string[] }) {
  return rows.length ? <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{fields.map(field => <th className="border-b px-2 py-1 font-medium" key={field}>{field}</th>)}</tr></thead><tbody>{rows.map((item, index) => { const row = (item && typeof item === 'object' ? item : {}) as Row; return <tr key={String(row.id ?? row.turn_id ?? row.event_id ?? index)}>{fields.map(field => <td className="max-w-xs truncate border-b px-2 py-1" title={text(row[field])} key={field}>{text(row[field])}</td>)}</tr>; })}</tbody></table></div> : <p className="text-sm opacity-60">暂无已保存记录</p>;
}

function RecordPanel({ title, path, fields }: { title: string; path: string; fields: string[] }) {
  const query = useQuery({ queryKey: [path], queryFn: ({ signal }) => api<{ items?: unknown[]; latest?: unknown }>(path, signal), refetchInterval: 5000, retry: false });
  const rows = query.data?.items || (query.data?.latest ? [query.data.latest] : []);
  return <section className="rounded-lg border p-4"><h2 className="mb-3 font-semibold">{title}</h2>{query.isPending ? <p>读取中…</p> : query.error ? <p className="text-red-600">{query.error.message}</p> : <Table rows={rows} fields={fields} />}</section>;
}

function RawDetails({ label, value }: { label: string; value: unknown }) {
  const [open, setOpen] = useState(false);
  return <details className="mt-2 text-xs" onToggle={event => setOpen(event.currentTarget.open)}><summary>{label}</summary>{open && <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap">{text(value)}</pre>}</details>;
}

function ResourcePanel({ runId }: { runId: string }) {
  const query = useQuery({ queryKey: ['resources', runId], queryFn: ({ signal }) => api<{ items?: unknown[] }>(`/api/runs/${encodeURIComponent(runId)}/resources`, signal), refetchInterval: 5000, retry: false });
  const rows = (query.data?.items || []) as Row[];
  const resource = rows.find(row => row.kind === 'resources');
  const data = resource?.data as Row | undefined;
  const inspect = data?.inspect as Row | undefined;
  const state = inspect?.State as Row | undefined;
  const usage = (data?.usage || data?.stats || data?.sample) as Row | undefined;
  const live = (data?.live || data) as Row | undefined;
  const supervisor = data?.supervisor as Row | undefined;
  const limits = supervisor?.values as Row | undefined;
  let docker: Row | undefined;
  let statsError: string | undefined;
  if (typeof live?.stats_stdout === 'string' && live.stats_stdout.trim()) {
    try { docker = JSON.parse(live.stats_stdout); }
    catch (error) { statsError = `Docker stats 解析失败：${String(error)}`; }
  }
  return <section className="rounded-lg border p-4"><h2 className="mb-3 font-semibold">资源 / 原生证据</h2>{query.isPending ? <p>读取中…</p> : query.error ? <p className="text-red-600">{query.error.message}</p> : !rows.length ? <p className="text-sm opacity-60">暂无已保存资源事实</p> : <>
    <dl className="grid gap-2 text-sm md:grid-cols-2"><div><dt className="opacity-60">来源</dt><dd>{text(resource?.source)}</dd></div><div><dt className="opacity-60">采样 / 终态时点</dt><dd>{text(data?.as_of ?? data?.observed_at ?? state?.FinishedAt ?? state?.StartedAt)}</dd></div><div><dt className="opacity-60">CPU</dt><dd>{text(usage?.cpu ?? usage?.cpu_percent ?? data?.cpu ?? docker?.CPUPerc ?? '未知')}</dd></div><div><dt className="opacity-60">RSS / 内存</dt><dd>{text(usage?.rss ?? usage?.memory ?? data?.rss ?? docker?.MemUsage ?? '未知')}</dd></div><div><dt className="opacity-60">I/O</dt><dd>{text(usage?.io ?? data?.io ?? docker?.BlockIO ?? '未知')}</dd></div><div><dt className="opacity-60">PID / 线程</dt><dd>{text(docker?.PIDs ?? '未知')}</dd></div></dl>
    {statsError && <p className="mt-2 text-red-600">{statsError}</p>}
    {limits && <div className="mt-3 text-sm"><p>公共资源采样（非历史峰值）：内存 {limits['memory.current'] == null ? '未知' : `${Math.round(Number(limits['memory.current']) / 1048576)} MiB`}；PID / 线程 {text(limits['pids.current'])} / {text(limits['pids.max'])}。</p><p className="text-xs opacity-70">{text(supervisor?.source)} · {timestamp(Number(supervisor?.observed_at_ns) / 1e9)}</p><RawDetails label="资源上限、触顶事件和采样错误" value={supervisor} /></div>}
    {state && <p className="mt-3 text-xs opacity-70">容器终态：{text(state.Status)}；ExitCode={text(state.ExitCode)}。此处不是历史峰值。</p>}
    {rows.filter(row => row.kind !== 'resources').map((row, index) => <RawDetails key={index} label={`${text(row.kind)} · ${text(row.source)}`} value={row.data} />)}
    <RawDetails label="展开完整资源原件" value={data} />
  </>}</section>;
}

function NativePanel({ runId }: { runId: string }) {
  const query = useQuery({ queryKey: ['native', runId], queryFn: ({ signal }) => api<{ items?: unknown[] }>(`/api/runs/${encodeURIComponent(runId)}/resources`, signal), refetchInterval: 5000, retry: false });
  const native = ((query.data?.items || []) as Row[]).find(row => row.kind === 'native');
  const data = native?.data as Row | undefined;
  const sessions = Array.isArray(data?.sessions) ? data.sessions as Row[] : [];
  const messages = Array.isArray(data?.session_messages) ? data.session_messages as Row[] : [];
  const errors = Array.isArray(data?.reader_errors) ? data.reader_errors : [];
  const session = [...sessions].sort((a, b) => Number(b.last_activity_at ?? 0) - Number(a.last_activity_at ?? 0))[0];
  const latest = messages[messages.length - 1];
  const error = errors[errors.length - 1] ?? (latest?.error ? latest.error : null);
  return <section className="rounded-lg border p-4"><h2 className="mb-3 font-semibold">Native session</h2>{query.isPending ? <p>读取中…</p> : !native ? <p className="text-sm opacity-60">暂无已保存 native 事实</p> : <>
    <dl className="grid gap-2 text-sm md:grid-cols-2"><div><dt className="opacity-60">来源</dt><dd>{text(native.source)} <span className="opacity-60">(retained)</span></dd></div><div><dt className="opacity-60">session identity</dt><dd>{text(session?.session_id)}</dd></div><div><dt className="opacity-60">最近保存的原生 state</dt><dd>{text(session?.state)}</dd></div><div><dt className="opacity-60">last activity</dt><dd>{text(session?.last_activity_at)}</dd></div></dl>
    <p className="mt-2 text-xs opacity-70">原生 state 不代表进程仍存活；是否正在运行以顶部 run lifecycle 为准。</p>
    <div className="mt-3 text-sm"><strong>最新保存事件 / 错误</strong><pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap">{text(error ?? latest ?? '未保存错误')}</pre></div>
    <RawDetails label="展开完整 native 原件（含 retained 历史）" value={data} />
  </>}</section>;
}

function CostPanel({ runId }: { runId: string }) {
  const query = useQuery({ queryKey: ['cost', runId], queryFn: ({ signal }) => api<{ items?: unknown[] }>(`/api/runs/${encodeURIComponent(runId)}/cost`, signal), refetchInterval: 5000, retry: false });
  const row = ((query.data?.items || []) as Row[])[0];
  const usage = (row?.data as Row | undefined)?.usage as Row | undefined;
  const providerUsage = (row?.data as Row | undefined)?.provider_usage as Row | undefined;
  const attempts = (providerUsage?.attempts || []) as Row[];
  return <section className="rounded-lg border p-4"><h2 className="mb-3 font-semibold">费用 / 原生用量</h2>{query.isPending ? <p>读取中…</p> : <dl className="grid gap-2 text-sm md:grid-cols-2"><div><dt className="opacity-60">状态</dt><dd>{text(row?.status ?? 'unknown')}</dd></div><div><dt className="opacity-60">金额</dt><dd>{text(row?.amount ?? row?.value ?? '未知')}</dd></div><div><dt className="opacity-60">来源 / scope</dt><dd>{text(row?.source ?? 'records/status.json')} · {text(row?.scope)}</dd></div><div><dt className="opacity-60">类型 / as_of</dt><dd>{text(row?.kind)} · {timestamp(row?.as_of)}</dd></div><div className="md:col-span-2"><dt className="opacity-60">原因 / 边界</dt><dd>{text(row?.reason ?? row?.note ?? (row ? '未保存 spend 原因' : '未保存 spend 事实；不能从运行生命周期推导费用'))}</dd></div></dl>}
    {usage && <><p className="mt-3 text-xs opacity-70">已记录的原生 token 用量（{text(usage.status)}），不是供应商账单。</p><Table rows={(usage.items || []) as unknown[]} fields={['model', 'provider', 'messages', 'tokens']} /><RawDetails label="用量来源、时段与缺口" value={usage} /></>}
    {providerUsage && <><p className="mt-3 text-xs opacity-70">供应商实际尝试与返回用量（{text(providerUsage.status)}）：{attempts.length} 次尝试，{attempts.filter(attempt => attempt.usage_status === 'recorded').length} 次返回用量；不是账单或套餐余额。下表显示最近8次尝试。</p><Table rows={attempts.slice(-8)} fields={['request_id', 'deployment_id', 'http_status', 'usage_status', 'usage']} /><RawDetails label="全部供应商尝试及采集缺口" value={providerUsage} /></>}
  </section>;
}

function LogPanel({ runId, storageRoot }: { runId: string; storageRoot?: string }) {
  const query = useQuery({ queryKey: ['logs', runId], queryFn: ({ signal }) => api<{ items?: unknown[] }>(`/api/runs/${encodeURIComponent(runId)}/logs`, signal), refetchInterval: 5000, retry: false });
  const rows = (query.data?.items || []) as Row[];
  return <section className="rounded-lg border p-4"><h2 className="mb-3 font-semibold">日志</h2><p className="mb-2 text-xs opacity-70">原文时间保留生产者时区，带 Z 的时间为 UTC；页面格式化时间显示本地时区。</p>{query.isPending ? <p>读取中…</p> : !rows.length ? <p className="text-sm opacity-60">暂无已保存日志摘要</p> : <div className="space-y-2">{rows.map((row, index) => <details key={index}><summary className="cursor-pointer text-sm">{text(row.source)} · {row.bytes == null ? '字节数未保存' : `${row.bytes} bytes`}{row.truncated === true ? ' · 仅末尾 65,536 bytes' : ''}</summary>{storageRoot && typeof row.source === 'string' && <p className="mt-2 break-all text-xs">完整原件位于保存宿主：<code>{storageRoot}/{row.source}</code></p>}<pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap text-xs">{text(row.tail ?? row.error ?? '无尾部内容')}</pre></details>)}</div>}</section>;
}

function BraidMount({ runId }: { runId: string }) {
  return <section className="rounded-lg border-2 border-indigo-200 p-2"><iframe title="Braid 原生过程视图" className="h-[72rem] w-full rounded" src={`/braid-viewer.html?run=${encodeURIComponent(runId)}`} /></section>;
}

export default function RunOverview({ runId, currentRun }: Props) {
  const detail = useQuery({ queryKey: ['run-detail', runId], queryFn: ({ signal }) => api<Row>(`/api/runs/${encodeURIComponent(runId)}`, signal), refetchInterval: 5000, retry: false });
  const status = detail.data?.status as Row | undefined;
  const native = status?.native as Row | undefined;
  const braid = native?.braid as Row | undefined;
  const saved = (detail.data?.record_summaries as Row | undefined)?.['result-save'] as Row | undefined;
  const storageRoot = typeof saved?.storage_root === 'string' ? saved.storage_root : undefined;
  const workspace = (detail.data?.record_summaries as Row | undefined)?.workspace as Row | undefined;
  return <div className="space-y-4"><section className="rounded-lg border p-5"><h1 className="text-xl font-semibold">{currentRun.label}</h1><p className="text-sm opacity-70">{runId}</p><dl className="mt-3 grid gap-2 text-sm md:grid-cols-4"><div><dt className="opacity-60">lifecycle</dt><dd>{text(status?.lifecycle ?? currentRun.lifecycle)}</dd></div><div><dt className="opacity-60">activity</dt><dd>{text(status?.activity ?? currentRun.activity)}</dd></div><div><dt className="opacity-60">as_of</dt><dd>{timestamp(status?.as_of ?? currentRun.as_of)}</dd></div><div><dt className="opacity-60">variant</dt><dd>{text(detail.data?.variant ?? currentRun.variant ?? currentRun.facts?.variant)}</dd></div>
      <div><dt className="opacity-60">目标 / 任务</dt><dd>{text(detail.data?.target)} / {text(detail.data?.task)}</dd></div><div><dt className="opacity-60">模型配方</dt><dd>{text(detail.data?.model_recipe)}</dd></div><div><dt className="opacity-60">来源 run</dt><dd>{text(detail.data?.source_run)}</dd></div><div><dt className="opacity-60">参赛</dt><dd>{text(detail.data?.competition)}</dd></div>
    </dl>{storageRoot && <div className="mt-3 break-all text-sm"><p>应用保存位置（回执所在宿主，不是 Console 服务器）：<code>{storageRoot}/data/workspace</code></p><p className="text-xs opacity-70">保存状态：{text(saved?.saved)}；Console 当前未提供 workspace 文件内容浏览或下载。</p></div>}{workspace && <details className="mt-3"><summary>已保存应用文件清单{workspace.truncated === true ? '（仅前500个文件，已截断）' : ''}</summary><p className="my-2 text-xs opacity-70">排除目录：{text(workspace.excluded_directories)}；保存时点：{timestamp(workspace.as_of)}。这是文件定位，不是内容预览。</p><Table rows={(workspace.files || []) as unknown[]} fields={['path', 'bytes', 'symlink']} />{Array.isArray(workspace.errors) && workspace.errors.length > 0 && <p className="text-red-600">{text(workspace.errors)}</p>}</details>}<RawDetails label="模型路由与结果保存回执" value={{ routes: detail.data?.model_routes, result_save: saved }} /></section>
    <div className="grid gap-4 md:grid-cols-2"><ResourcePanel runId={runId} /><NativePanel runId={runId} /><LogPanel runId={runId} storageRoot={storageRoot} /><CostPanel runId={runId} /><RecordPanel title="评测" path={`/api/runs/${encodeURIComponent(runId)}/evaluations`} fields={['kind', 'status', 'score', 'source']} /></div>{(braid?.available === true || isBraidRun(currentRun)) && <BraidMount runId={runId} />}</div>;
}
