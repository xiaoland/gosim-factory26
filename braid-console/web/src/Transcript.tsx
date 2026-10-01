import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { RotateCw } from 'lucide-react';
import { ActionButton, EmptyState, LoadingSkeleton, Notice, Row, StatusBadge } from '@/components/console-ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { type NativeEntry, type ProviderSession, type TranscriptPage } from './api';
import { api, url } from './http';
import { Markdown } from './Markdown';

type ObjectValue = Record<string, unknown>;
type Mode = 'chat' | 'trace' | 'files';
type TraceLink = (offset: number) => void;
function object(value: unknown): ObjectValue | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as ObjectValue : null;
}
function json(value: unknown) { return JSON.stringify(value, null, 2) ?? '未记录'; }
function text(value: unknown) { return typeof value === 'string' ? value : json(value); }
function nativePayload(entry: NativeEntry) {
  const value = object(entry.value) || {};
  if (value.type === 'message') return object(value.message);
  if (value.type !== 'response_item') return null;
  const payload = object(value.payload);
  return payload && ['message', 'function_call', 'function_call_output', 'reasoning'].includes(String(payload.type)) ? payload : null;
}
function blocks(content: unknown): unknown[] {
  return Array.isArray(content) ? content : content == null ? [] : [content];
}
function isText(value: unknown) {
  const block = object(value);
  return typeof value === 'string' || !!(block && ['text', 'input_text', 'output_text'].includes(String(block.type)) && typeof block.text === 'string');
}
function isThinking(value: unknown) { return ['thinking', 'reasoning'].includes(String(object(value)?.type)); }
function isCall(value: unknown) { return ['toolCall', 'function_call'].includes(String(object(value)?.type)); }
function callId(block: ObjectValue) { return String(block.type === 'function_call' ? block.call_id || '' : block.id || ''); }
function isResult(payload: ObjectValue | null) { return payload?.role === 'toolResult' || payload?.type === 'function_call_output'; }
function nativeError(payload: ObjectValue | null) {
  if (!payload) return null;
  if (payload.errorMessage != null) return text(payload.errorMessage) || '原生 errorMessage 为空；请查看完整记录。';
  if (payload.error) return text(payload.error);
  return payload.stopReason === 'error' ? 'stopReason=error；原生记录未提供错误详情。' : null;
}
function timestamp(entry: NativeEntry) { return String(entry.value?.timestamp ?? nativePayload(entry)?.timestamp ?? '未记录时间'); }

function Source({ entry, onTrace, label = '查看 Trace' }: { entry: NativeEntry; onTrace: TraceLink; label?: string }) {
  return <Row className="chat-source" align="center" gap={8} wrap><span className="muted">{timestamp(entry)} · 字节 {entry.offset}</span>
    <ActionButton variant="ghost" size="sm" onClick={() => onTrace(entry.offset)}>{label}</ActionButton></Row>;
}
function NativeBlock({ value, trace = false }: { value: unknown; trace?: boolean }) {
  const block = object(value);
  if (isText(value)) return <Markdown body={typeof value === 'string' ? value : String(block?.text)} />;
  if (isCall(value)) return <details className="native-tool" open={trace || undefined}><summary>工具调用 · {String(block?.name || '未记录')} <code>{block && callId(block)}</code></summary>
    <pre className="native-code">{text(block?.arguments)}</pre></details>;
  if (isThinking(value)) return <details className="native-thinking"><summary>思考内容</summary>
    <pre className="native-code">{text(block?.thinking ?? block?.text ?? block)}</pre></details>;
  return <details className="native-metadata"><summary>非文本 / 未解释内容 · {String(block?.type || '未知类型')}</summary><pre className="native-code">{text(value)}</pre></details>;
}
function ResultContent({ payload }: { payload: ObjectValue }) {
  return <>{blocks(payload.content).map((block, index) => <pre className="native-code" key={index}>{isText(block) ? typeof block === 'string' ? block : String(object(block)?.text) : text(block)}</pre>)}
    {payload.output != null && <pre className="native-code">{text(payload.output)}</pre>}
    {payload.content == null && payload.output == null && <pre className="native-code">{json(payload)}</pre>}</>;
}
function TraceRecord({ entry }: { entry: NativeEntry }) {
  if (entry.error) return <Notice tone="error" title={`JSONL 字节 ${entry.offset} 解析失败`} description={<><pre className="native-code">{entry.error}</pre><pre className="native-code">{entry.raw}</pre></>} />;
  const value = object(entry.value) || {};
  const payload = nativePayload(entry);
  const error = nativeError(payload);
  return <><Row className="trace-entry-head" align="center" gap={8} wrap><StatusBadge tone={payload?.isError === true || error ? 'error' : 'default'}>{String(value.type || '原生记录')}</StatusBadge>
    {payload && <strong>{String(payload.role || payload.type || '')}</strong>}<span className="muted">{timestamp(entry)} · 字节 {entry.offset}</span>
    {payload?.isError === true && <StatusBadge tone="error">isError=true</StatusBadge>}</Row>
    {payload && <div className="native-entry-body">{isResult(payload) ? <ResultContent payload={payload} /> : payload.type === 'function_call' || payload.type === 'reasoning'
      ? <NativeBlock value={payload} trace /> : blocks(payload.content).map((block, index) => <NativeBlock key={index} value={block} trace />)}
      {error && <Notice tone="error" title="原生错误" description={<pre className="native-code">{error}</pre>} />}</div>}
    <details className="native-raw"><summary>完整原生记录</summary><pre className="native-code">{json(entry.value)}</pre></details></>;
}

interface LocatedEntry { entry: NativeEntry; payload: ObjectValue | null; segment: number; boundary?: string }
interface ToolCall { entry: NativeEntry; block: ObjectValue; key: string; id: string; segment: number }
interface ToolResult { entry: NativeEntry; payload: ObjectValue; id: string; segment: number }
interface ToolAssociation { result?: ToolResult; ambiguous: boolean }
interface Activity { key: string; kind: 'thinking' | 'tool' | 'notification' | 'unknown' | 'result'; entry: NativeEntry; value: unknown; call?: ToolCall; association?: ToolAssociation; reason?: string }
type ChatItem = { kind: 'activities'; key: string; activities: Activity[] }
  | { kind: 'message'; key: string; entry: NativeEntry; role: 'user' | 'assistant'; content: unknown[] }
  | { kind: 'error'; key: string; entry: NativeEntry; title: string; error?: string; result?: ObjectValue }
  | { kind: 'boundary'; key: string; entry: NativeEntry; label: string };

function conversation(entries: NativeEntry[]) {
  let segment = 0;
  let previousId: string | undefined;
  const located: LocatedEntry[] = entries.map(entry => {
    const value = object(entry.value) || {};
    let boundary: string | undefined;
    if (entry.error) { segment++; previousId = undefined; }
    else if (value.type === 'compaction' || value.type === 'branch_summary') {
      segment++;
      boundary = value.type === 'compaction' ? '上下文压缩' : '分支摘要';
    } else if ('parentId' in value && previousId !== undefined && value.parentId !== previousId) {
      segment++;
      boundary = `父链不连续：parentId=${text(value.parentId)}，上一条记录 id=${previousId}`;
    }
    // All native chain entries participate, including events omitted from the chat view.
    if (value.type !== 'session' && typeof value.id === 'string') previousId = value.id;
    return { entry, payload: nativePayload(entry), segment, boundary };
  });
  const calls = new Map<string, ToolCall[]>();
  const results = new Map<string, ToolResult[]>();
  const callByBlock = new Map<string, ToolCall>();
  for (const item of located) {
    const { entry, payload, segment } = item;
    if (!payload) continue;
    const content = payload.type === 'function_call' ? [payload] : blocks(payload.content);
    content.forEach((value, index) => {
      if (!isCall(value)) return;
      const block = object(value)!;
      const id = callId(block);
      const call = { entry, block, key: `${entry.offset}:${index}`, id, segment };
      callByBlock.set(call.key, call);
      if (id) { const key = `${segment}:${id}`; calls.set(key, [...(calls.get(key) || []), call]); }
    });
    if (isResult(payload)) {
      const id = String(payload.toolCallId || payload.call_id || '');
      if (id) { const key = `${segment}:${id}`; results.set(key, [...(results.get(key) || []), { entry, payload, id, segment }]); }
    }
  }
  const associations = new Map<string, ToolAssociation>();
  const pairedResults = new Set<number>();
  for (const call of callByBlock.values()) {
    const key = `${call.segment}:${call.id}`;
    const matchingCalls = calls.get(key) || [];
    const matchingResults = results.get(key) || [];
    const ambiguous = matchingCalls.length > 1 || matchingResults.length > 1;
    const result = !ambiguous && matchingResults.length === 1 && matchingResults[0].entry.offset > call.entry.offset ? matchingResults[0] : undefined;
    associations.set(call.key, { result, ambiguous });
    if (result) pairedResults.add(result.entry.offset);
  }
  const items: ChatItem[] = [];
  let activities: Activity[] = [];
  function flush() { if (activities.length) { items.push({ kind: 'activities', key: `activity:${activities[0].key}`, activities }); activities = []; } }
  function add(item: Exclude<ChatItem, { kind: 'activities' }>) { flush(); items.push(item); }
  for (const { entry, payload, segment, boundary } of located) {
    const value = object(entry.value) || {};
    if (boundary) add({ kind: 'boundary', key: `boundary:${entry.offset}`, entry, label: boundary });
    if (entry.error) {
      add({ kind: 'error', key: `parse:${entry.offset}`, entry, title: 'JSONL 解析失败', error: entry.error });
      continue;
    }
    if (value.type === 'compaction' || value.type === 'branch_summary') continue;
    if (value.type === 'custom_message') {
      activities.push({ key: `notification:${entry.offset}`, kind: 'notification', entry, value });
      continue;
    }
    if (!payload) {
      if (!['session', 'session_meta', 'model_change', 'thinking_level_change'].includes(String(value.type))) {
        activities.push({ key: `unknown:${entry.offset}`, kind: 'unknown', entry, value: entry.value });
      }
      continue;
    }
    if (isResult(payload)) {
      if (payload.isError === true || nativeError(payload)) add({ kind: 'error', key: `tool-error:${entry.offset}`, entry,
        title: `工具错误 · ${String(payload.toolName || payload.name || '未记录工具名')}`, error: nativeError(payload) || 'isError=true', result: payload });
      if (!pairedResults.has(entry.offset)) {
        const id = String(payload.toolCallId || payload.call_id || '');
        const matchingCalls = calls.get(`${segment}:${id}`) || [];
        const matchingResults = results.get(`${segment}:${id}`) || [];
        activities.push({ key: `result:${entry.offset}`, kind: 'result', entry, value: payload,
          reason: matchingCalls.length > 1 || matchingResults.length > 1 ? '关联有歧义；保留独立结果' : '已加载的同一父链区间内未找到可确认的先前调用' });
      }
      continue;
    }
    const content = payload.type === 'function_call' || payload.type === 'reasoning' ? [payload] : blocks(payload.content);
    if (payload.role === 'user') {
      add({ kind: 'message', key: `user:${entry.offset}`, entry, role: 'user', content });
    } else if (payload.role === 'assistant' || payload.type === 'function_call' || payload.type === 'reasoning') {
      content.forEach((block, index) => {
        const key = `${entry.offset}:${index}`;
        if (isText(block) && (typeof block === 'string' ? block : object(block)?.text)) {
          add({ kind: 'message', key: `assistant:${key}`, entry, role: 'assistant', content: [block] });
        } else if (isCall(block)) {
          const call = callByBlock.get(key)!;
          activities.push({ key, kind: 'tool', entry, value: block, call, association: associations.get(key) });
        } else if (isThinking(block)) activities.push({ key, kind: 'thinking', entry, value: block });
        else if (!isText(block)) activities.push({ key, kind: 'unknown', entry, value: block });
      });
      if (!content.length && !nativeError(payload)) activities.push({ key: `empty:${entry.offset}`, kind: 'unknown', entry, value: payload, reason: '原生 assistant 未提供正文或活动内容' });
    } else activities.push({ key: `payload:${entry.offset}`, kind: 'unknown', entry, value: payload, reason: '此原生消息类型尚未解释' });
    const error = nativeError(payload);
    if (error) add({ kind: 'error', key: `error:${entry.offset}`, entry, title: 'Agent 原生错误', error });
  }
  flush();
  return items;
}

function ToolActivity({ activity, onTrace }: { activity: Activity; onTrace: TraceLink }) {
  const call = activity.call!;
  const association = activity.association;
  const result = association?.result;
  const failed = result?.payload.isError === true || !!nativeError(result?.payload || null);
  const state = association?.ambiguous ? '关联有歧义；查看独立结果' : result ? '已返回' : '已加载记录中未见结果';
  return <article className={`chat-tool ${failed ? 'native-failed' : ''}`}><Row className="chat-tool-head" align="center" gap={8} wrap>
    <strong>{String(call.block.name || '未记录工具名')}</strong><StatusBadge className="chat-tool-status" tone={failed ? 'error' : result ? 'cyan' : 'default'}>{state}</StatusBadge>
    {failed && <StatusBadge tone="error">工具错误</StatusBadge>}</Row>
    <Source entry={call.entry} onTrace={onTrace} label="调用 Trace" />
    {!!call.id && <code>{call.id}</code>}
    <details className="native-tool"><summary>调用参数</summary><pre className="native-code">{text(call.block.arguments)}</pre></details>
    {result && <details className="native-result"><summary>工具结果{failed ? ' · 错误' : ''}</summary><Source entry={result.entry} onTrace={onTrace} label="结果 Trace" />
      <ResultContent payload={result.payload} />
      {nativeError(result.payload) && <pre className="native-code">{nativeError(result.payload)}</pre>}
      <details className="native-raw"><summary>完整结果记录</summary><pre className="native-code">{json(result.entry.value)}</pre></details>
    </details>}</article>;
}
function ActivityGroup({ activities, onTrace }: { activities: Activity[]; onTrace: TraceLink }) {
  const tools = activities.filter(activity => activity.kind === 'tool');
  const thoughts = activities.filter(activity => activity.kind === 'thinking').length;
  const notifications = activities.filter(activity => activity.kind === 'notification').length;
  const other = activities.length - tools.length - thoughts - notifications;
  const failures = tools.filter(activity => activity.association?.result?.payload.isError === true || nativeError(activity.association?.result?.payload || null)).length;
  const names = [...new Set(tools.map(activity => String(activity.call?.block.name || '未记录工具名')))];
  return <details className="chat-activities"><summary>过程活动 · {[tools.length && `${tools.length} 次工具调用（${names.join('、')}）`, thoughts && `${thoughts} 段思考`, notifications && `${notifications} 条通知`, other && `${other} 条其它内容`].filter(Boolean).join(' · ')}
    {!!failures && <StatusBadge tone="error">{failures} 项工具错误</StatusBadge>}</summary>
    <div className="chat-activity-body">{activities.map(activity => activity.kind === 'tool' ? <ToolActivity key={activity.key} activity={activity} onTrace={onTrace} />
      : <div key={activity.key} className={activity.kind === 'notification' ? 'chat-notification' : 'chat-activity'}>
        <Source entry={activity.entry} onTrace={onTrace} />
        {activity.reason && <p className="warning-text">{activity.reason}</p>}
        {activity.kind === 'result' ? <><strong>独立工具结果 · {String(object(activity.value)?.toolName || object(activity.value)?.name || '')}</strong>
          <ResultContent payload={object(activity.value)!} /></>
          : activity.kind === 'notification' ? <details><summary>通知 · {String(object(activity.value)?.customType || '原生通知')}{object(activity.value)?.display === false ? ' · 后台通知（display=false）' : ''}</summary>
            {blocks(object(activity.value)?.content).map((block, index) => <NativeBlock value={block} key={index} />)}
            <details className="native-raw"><summary>完整通知</summary><pre className="native-code">{json(activity.value)}</pre></details></details>
            : <NativeBlock value={activity.value} />}
      </div>)}</div></details>;
}
function ChatRecord({ item, onTrace }: { item: ChatItem; onTrace: TraceLink }) {
  if (item.kind === 'activities') return <ActivityGroup activities={item.activities} onTrace={onTrace} />;
  if (item.kind === 'boundary') return <div className="chat-boundary"><Notice tone="info" title={item.label}
    description="按文件顺序读取历史；此处停止跨边界合并活动和工具配对。" /><Source entry={item.entry} onTrace={onTrace} />
    <details className="native-raw"><summary>边界原生记录</summary><pre className="native-code">{json(item.entry.value)}</pre></details></div>;
  if (item.kind === 'error') return <div className="chat-error"><Notice tone="error" title={item.title} description={<>
    {item.error && <pre className="native-code">{item.error}</pre>}
    {item.result && <ResultContent payload={item.result} />}
    {item.entry.raw && <pre className="native-code">{item.entry.raw}</pre>}</>} /><Source entry={item.entry} onTrace={onTrace} /></div>;
  return <article className={`chat-message ${item.role === 'user' ? 'chat-input' : 'chat-assistant'}`}><Row className="chat-message-head" align="center" justify="space-between" gap={8} wrap>
    <strong>{item.role === 'user' ? '输入' : 'Agent'}</strong><Source entry={item.entry} onTrace={onTrace} /></Row>
    <div className="chat-message-body">{item.content.length ? item.content.map((block, index) => <NativeBlock value={block} key={index} />)
      : <p className="muted">原生输入未提供内容；可查看 Trace。</p>}</div></article>;
}

export default function Transcript({ run, record, files }: { run: string; record: ProviderSession; files?: ReactNode }) {
  const [mode, setMode] = useState<Mode>('chat');
  const [filesVisited, setFilesVisited] = useState(false);
  const [selectedOffset, setSelectedOffset] = useState<number | null>(null);
  const root = useRef<HTMLElement>(null);
  const traceRefs = useRef(new Map<number, HTMLElement>());
  const scrollPositions = useRef<Partial<Record<Mode, number>>>({});
  const pendingTrace = useRef<number | null>(null);
  const query = useInfiniteQuery({
    queryKey: ['transcript', run, record.record_id], initialPageParam: 0,
    queryFn: ({ signal, pageParam }) => api<TranscriptPage>(url('/api/transcript', { run, provider: record.record_id, offset: pageParam }), signal),
    getNextPageParam: (page, _pages, offset) => page.eof || page.next_offset === offset ? undefined : page.next_offset, retry: false,
  });
  const pages = query.data?.pages;
  const last = pages?.at(-1);
  const entries = useMemo(() => pages?.flatMap(page => page.entries) || [], [pages]);
  const items = useMemo(() => conversation(entries), [entries]);
  function changeMode(next: Mode) {
    if (next === mode) return;
    if (root.current?.getClientRects().length) scrollPositions.current[mode] = window.scrollY;
    if (next === 'files') setFilesVisited(true);
    setMode(next);
  }
  function showTrace(offset: number) {
    pendingTrace.current = offset;
    setSelectedOffset(offset);
    changeMode('trace');
  }
  useLayoutEffect(() => {
    if (!root.current?.getClientRects().length) return;
    if (mode === 'trace' && pendingTrace.current !== null) {
      const target = traceRefs.current.get(pendingTrace.current);
      if (target?.getClientRects().length) {
        target.scrollIntoView({ block: 'start' });
        target.focus({ preventScroll: true });
        pendingTrace.current = null;
      }
    } else if (scrollPositions.current[mode] !== undefined) window.scrollTo({ top: scrollPositions.current[mode] });
  }, [mode, selectedOffset]);
  const pagination = <Row className="native-pagination" align="center" justify="space-between" gap={12} wrap>
    <span className="muted">{last ? `已加载 ${entries.length} 条记录 · 字节 [0, ${last.next_offset}) / 当前文件 ${last.size} 字节${last.eof ? ' · 已到本次读取的文件末尾' : ' · 当前显示会话开头，后面还有记录'}${last.waiting ? ' · 末尾记录尚未写完整' : ''}` : '从会话开头读取；每批最多 50 条，按 1 MiB 边界读取（完整记录不截断）。'}</span>
    <Row align="center" gap={8} wrap><ActionButton icon={<RotateCw />} pending={query.isFetching && !query.isFetchingNextPage} disabled={query.isFetchingNextPage} onClick={() => { void query.refetch(); }}>刷新已加载内容</ActionButton>
      {query.hasNextPage && <ActionButton pending={query.isFetchingNextPage} disabled={query.isFetching && !query.isFetchingNextPage} onClick={() => { void query.fetchNextPage(); }}>{last?.waiting ? '重新读取末尾后续' : '加载后续记录'}</ActionButton>}</Row>
  </Row>;
  return <section ref={root} className="native-transcript" aria-label="Provider Session 阅读">
    <Tabs className="session-transcript-tabs" value={mode} onValueChange={value => changeMode(value as Mode)}><TabsList aria-label="Provider Session 内容"><TabsTrigger value="chat">对话</TabsTrigger><TabsTrigger value="trace">Trace</TabsTrigger>{files !== undefined && <TabsTrigger value="files">文件</TabsTrigger>}</TabsList>
      <div className="transcript-toolbar" hidden={mode === 'files'}>{pagination}
        <p className="subtle">按文件顺序读取已加载历史；局部末条不代表最新进展。原生凭据由现有 reader 脱敏。</p>
        {query.error && <Notice className="error-alert" tone="error" title="原生文件读取失败；已加载内容不能证明当前状态" description={<pre className="native-code">{query.error.message}</pre>} />}
        {query.isPending && <LoadingSkeleton rows={6} />}
      </div>
      <TabsContent value="chat" forceMount hidden={mode !== 'chat'} className="transcript-chat">{items.map(item => <ChatRecord key={item.key} item={item} onTrace={showTrace} />)}
        {!query.isPending && !query.error && !entries.length && <EmptyState description={last?.waiting ? '文件末尾记录尚未写完整，请稍后刷新' : '原生文件没有记录'} />}
        {!!entries.length && !items.length && <EmptyState description="已加载记录只有会话元数据；Trace 保留全部原生记录，后续内容需继续加载。" />}
      </TabsContent>
      <TabsContent value="trace" forceMount hidden={mode !== 'trace'} className="transcript-trace">{entries.map(entry => <article key={entry.offset} tabIndex={-1}
        ref={element => { if (element) traceRefs.current.set(entry.offset, element); else traceRefs.current.delete(entry.offset); }}
        className={`trace-entry ${selectedOffset === entry.offset ? 'trace-selected' : ''}`}><TraceRecord entry={entry} /></article>)}
        {!query.isPending && !query.error && !entries.length && <EmptyState description={last?.waiting ? '文件末尾记录尚未写完整，请稍后刷新' : '原生文件没有记录'} />}
      </TabsContent>
      {filesVisited && <TabsContent value="files" forceMount hidden={mode !== 'files'} className="transcript-files">{files}</TabsContent>}
      <div hidden={mode === 'files'}>{last && pagination}</div>
    </Tabs>
  </section>;
}
