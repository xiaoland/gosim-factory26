import { ActionButton, CopyText, EmptyState, LoadingSkeleton, Notice, Row, StatusBadge } from '@/components/console-ui';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, url } from './http';
import { useState, type ReactNode } from 'react';
import { ArrowLeft, RotateCw } from 'lucide-react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { type NativeEntry, type ProviderSession, type Selection, type TranscriptPage } from './api';
import { routeURL } from './navigation';
import { Markdown } from './Markdown';

const coverage = '展示登记 CLI 可枚举的当前与历史记录；缺失 physical 材料的会话可能未列出。生命周期来自 Braid 记录，实际执行状态以页面上方的生成状态为准。';
const historical = (session: ProviderSession) => ['replaced', 'retired'].includes(session.status);
export function useSessions(run: string) {
  return useQuery({ queryKey: ['sessions', run], queryFn: ({ signal }) => api<ProviderSession[]>(url('/api/sessions', { run }), signal),
    enabled: !!run, refetchInterval: 5000, retry: false });
}
export function SessionLink({ run, selected, onSelect, children }: { run: string; selected: Selection; onSelect: (value: Selection) => void; children: ReactNode }) {
  return <a href={routeURL(run, selected)} onClick={event => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); onSelect(selected);
  }}>{children}</a>;
}
function itemSessions(records: ProviderSession[], selected: Selection) {
  return records.filter(record => record.work_item_kind === selected.kind && Number(record.work_item_id) === selected.id);
}
function SessionState({ session }: { session: ProviderSession }) {
  return <Row gap={4} wrap>{historical(session) && <StatusBadge>历史</StatusBadge>}<StatusBadge>{session.status}</StatusBadge></Row>;
}
export function SessionLinks({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useSessions(run);
  const records = itemSessions(query.data || [], selected);
  const groups = [...new Set(records.map(record => record.group_id).filter((id): id is string => !!id))];
  return <div className="metadata-section session-links"><div className="metadata-label">Braid agent sessions <span>{groups.length}</span></div>
    {query.error && <Notice tone="error" title="会话关系读取失败" description={<pre>{query.error.message}</pre>} />}
    {query.isPending ? <LoadingSkeleton rows={2} /> : groups.length ? groups.map(agent => {
      const providers = records.filter(record => record.group_id === agent);
      return <div className="session-link" key={agent}><SessionLink run={run} selected={{ kind: selected.kind, id: selected.id, agent }} onSelect={onSelect}>
        <strong>{[...new Set(providers.map(record => record.profile_id))].join(' / ')}</strong><code>{agent}</code>
      </SessionLink><span className="muted">{providers.length} 条 provider · {providers.filter(historical).length} 条历史</span></div>;
    }) : <span className="muted">未发现可枚举记录</span>}
    <p className="subtle">包括历史 provider；缺失 physical 材料的记录可能未列出。</p>
    {!!records.filter(record => !record.group_id).length && <span className="warning-text">存在未绑定 Braid agent 的记录。</span>}
  </div>;
}

function object(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;
}
function json(value: unknown) { return JSON.stringify(value, null, 2); }
function NativeBlock({ value }: { value: unknown }) {
  const block = object(value);
  if (!block) return <pre className="native-code">{typeof value === 'string' ? value : json(value)}</pre>;
  if (block.type === 'toolCall' || block.type === 'function_call') return <details className="native-tool" open>
    <summary>工具调用 · {String(block.name || '未记录')} <code>{String(block.id || block.call_id || '')}</code></summary>
    <pre className="native-code">{typeof block.arguments === 'string' ? block.arguments : json(block.arguments)}</pre>
  </details>;
  if (block.type === 'thinking' || block.type === 'reasoning') return <details className="native-thinking">
    <summary>思考内容</summary><pre className="native-code">{String(block.thinking || block.text || json(block))}</pre>
  </details>;
  if (typeof block.text === 'string') return <Markdown body={block.text} />;
  return <details><summary>原生内容 · {String(block.type || '未知类型')}</summary><pre className="native-code">{json(block)}</pre></details>;
}
function NativeRecord({ entry }: { entry: NativeEntry }) {
  if (entry.error) return <Notice tone="error" title={`JSONL 字节 ${entry.offset} 解析失败`} description={<><pre>{entry.error}</pre><pre className="native-code">{entry.raw}</pre></>} />;
  const value = entry.value || {};
  const payload = object(value.message) || (value.type === 'response_item' ? object(value.payload) : null);
  const role = payload?.role;
  const content = payload?.content;
  const tool = role === 'toolResult' || payload?.type === 'function_call_output';
  if (payload && (role || payload.type === 'function_call' || tool)) return <article className={`native-entry ${tool ? 'native-result' : ''} ${payload.isError ? 'native-failed' : ''}`}>
    <Row className="native-entry-head" gap={8} wrap><StatusBadge tone={tool ? payload.isError ? 'error' : 'cyan' : role === 'user' ? 'blue' : 'green'}>
      {tool ? '工具结果' : role === 'user' ? '用户' : role === 'assistant' ? 'Agent' : '工具调用'}</StatusBadge>
      {tool && <strong>{String(payload.toolName || payload.name || '')}</strong>}
      {!!(payload.toolCallId || payload.call_id) && <code>{String(payload.toolCallId || payload.call_id)}</code>}
      {!!payload.isError && <StatusBadge tone="error">isError=true</StatusBadge>}
      <span className="muted">{String(value.timestamp || payload.timestamp || '')} · 字节 {entry.offset}</span>
    </Row>
    <div className="native-entry-body">{Array.isArray(content) ? content.map((block, index) => tool
      ? <pre className="native-code" key={index}>{String(object(block)?.text ?? json(block))}</pre>
      : <NativeBlock key={index} value={block} />) : content ? <NativeBlock value={content} /> : payload.type === 'function_call' ? <NativeBlock value={payload} />
      : <pre className="native-code">{typeof payload.output === 'string' ? payload.output : json(payload)}</pre>}
      {!!(payload.errorMessage || payload.error) && <Notice tone="error" title="原生错误" description={<pre>{String(payload.errorMessage || json(payload.error))}</pre>} />}
      <details className="native-raw"><summary>完整原生记录</summary><pre className="native-code">{json(value)}</pre></details>
    </div>
  </article>;
  return <details className="native-metadata"><summary>{String(value.type || '原生事件')} · {String(value.timestamp || '')} · 字节 {entry.offset}</summary><pre className="native-code">{json(value)}</pre></details>;
}
function Transcript({ run, record }: { run: string; record: ProviderSession }) {
  const query = useInfiniteQuery({
    queryKey: ['transcript', run, record.record_id], initialPageParam: 0,
    queryFn: ({ signal, pageParam }) => api<TranscriptPage>(url('/api/transcript', { run, provider: record.record_id, offset: pageParam }), signal),
    getNextPageParam: page => page.eof ? undefined : page.next_offset, retry: false,
  });
  const pages = query.data?.pages || [];
  const last = pages.at(-1);
  const entries = pages.flatMap(page => page.entries);
  return <section className="native-transcript" aria-label="原生对话与工具调用">
    <Row align="center" justify="space-between" gap={12} wrap><h4>原生对话与工具调用</h4>
      <ActionButton icon={<RotateCw />} pending={query.isFetching} onClick={() => { void query.refetch(); }}>刷新已加载记录</ActionButton></Row>
    <span className="muted">按文件位置分批读取；工具参数、结果和错误保留原始内容，凭据字段脱敏。</span>
    {query.error && <Notice className="error-alert" tone="error" title="原生文件读取失败；会话元数据仍可查看" description={<pre>{query.error.message}</pre>} />}
    {query.isPending && <LoadingSkeleton rows={6} />}
    {entries.map(entry => <NativeRecord key={entry.offset} entry={entry} />)}
    {!query.isPending && !query.error && !entries.length && <EmptyState description={last?.waiting ? '文件末尾记录尚未写完整，请稍后刷新' : '原生文件没有记录'} />}
    {last && <Row className="native-pagination" gap={12} align="center" wrap><span className="muted">已加载 {entries.length} 条记录 · 字节 {last.next_offset} / {last.size}{last.eof ? ' · 已到当前文件末尾' : ''}</span>
      {query.hasNextPage && <ActionButton pending={query.isFetchingNextPage} onClick={() => { void query.fetchNextPage(); }}>{last.waiting ? '重新读取未完成的末尾' : '加载后续记录'}</ActionButton>}
    </Row>}
  </section>;
}

function TurnHistory({ provider }: { provider: ProviderSession }) {
  const [expanded, setExpanded] = useState(false);
  const [page, setPage] = useState(0);
  const turns = provider.turns || [];
  const pages = Math.ceil(turns.length / 50);
  return <details className="technical-details" onToggle={event => setExpanded(event.currentTarget.open)}>
    <summary>Turn 历史 <span className="muted">{provider.source_mode === 'archive' && !provider.turns ? '未保存' : `${turns.length} 条`}</span></summary>
    {expanded && <><Table className="session-table"><TableHeader><TableRow><TableHead>Braid turn / Provider turn</TableHead><TableHead>状态</TableHead><TableHead>触发</TableHead></TableRow></TableHeader>
      <TableBody>{turns.slice(page * 50, (page + 1) * 50).map(turn => <TableRow key={turn.braid_turn_id}><TableCell><code>{turn.braid_turn_id}</code><div className="subtle">{turn.provider_turn_id || 'Provider turn 未确认'}</div></TableCell><TableCell><StatusBadge>{turn.status}</StatusBadge></TableCell><TableCell>{turn.trigger_kind}</TableCell></TableRow>)}
        {!turns.length && <TableRow><TableCell colSpan={3} className="py-6 text-center muted">{provider.source_mode === 'archive' && !provider.turns ? 'Turn 历史未保存' : '暂无 Turn 记录'}</TableCell></TableRow>}
      </TableBody></Table>
      {pages > 1 && <Row className="table-pagination" align="center" justify="space-between"><span className="muted">第 {page + 1} / {pages} 页 · 每页 50 条</span>
        <Row><ActionButton size="sm" disabled={!page} onClick={() => setPage(page - 1)}>上一页</ActionButton><ActionButton size="sm" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>下一页</ActionButton></Row></Row>}
    </>}
  </details>;
}

function ProviderDirectory({ run, records, agent, onSelect }: { run: string; records: ProviderSession[]; agent: Selection; onSelect: (value: Selection) => void }) {
  const [scope, setScope] = useState('all');
  const [search, setSearch] = useState('');
  const needle = search.trim().toLowerCase();
  const visible = records.filter(record => (scope !== 'history' || historical(record)) && (!needle || `${record.record_id} ${record.native_session_id} ${record.profile_id} ${record.status}`.toLowerCase().includes(needle)));
  return <div className="provider-directory">
    <Row className="provider-toolbar" align="center" justify="space-between" wrap><Tabs value={scope} onValueChange={setScope}><TabsList aria-label="会话范围"><TabsTrigger value="all">全部 {records.length}</TabsTrigger><TabsTrigger value="history">历史 {records.filter(historical).length}</TabsTrigger></TabsList></Tabs>
      <Input aria-label="搜索会话身份或状态" placeholder="搜索会话身份或状态…" value={search} onChange={event => setSearch(event.target.value)} /></Row>
    <Table className="session-table"><TableHeader><TableRow><TableHead>Native session / Physical 记录</TableHead><TableHead>状态</TableHead><TableHead>Provider / Profile</TableHead><TableHead>Turns</TableHead></TableRow></TableHeader>
      <TableBody>{visible.map(record => <TableRow key={record.record_id}>
        <TableCell><SessionLink run={run} selected={{ ...agent, provider: record.record_id }} onSelect={onSelect}><code>{record.native_session_id || '原生身份未确认'}</code><div className="subtle">{record.record_id}</div></SessionLink></TableCell>
        <TableCell><SessionState session={record} /></TableCell><TableCell>{record.provider}<div className="subtle">{record.profile_id}</div></TableCell>
        <TableCell>{record.source_mode === 'archive' && !record.turns ? '未保存' : record.turns?.length || 0}</TableCell>
      </TableRow>)}{!visible.length && <TableRow><TableCell colSpan={4}><EmptyState description="没有符合条件的会话记录" /><ActionButton className="empty-reset" size="sm" onClick={() => { setScope('all'); setSearch(''); }}>清除筛选</ActionButton></TableCell></TableRow>}</TableBody>
    </Table>
  </div>;
}

export default function Sessions({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useSessions(run);
  const records = itemSessions(query.data || [], selected).filter(record => record.group_id === selected.agent);
  const provider = selected.provider ? records.find(record => record.record_id === selected.provider) : undefined;
  const item = { kind: selected.kind, id: selected.id };
  const agent = { ...item, agent: selected.agent };
  const label = `${selected.kind === 'pr' ? 'PR' : 'Issue'} #${selected.id}`;
  return <section className="detail-panel session-panel">
    <Breadcrumb><BreadcrumbList>
      <BreadcrumbItem><BreadcrumbLink asChild><SessionLink run={run} selected={item} onSelect={onSelect}>{label}</SessionLink></BreadcrumbLink></BreadcrumbItem><BreadcrumbSeparator />
      <BreadcrumbItem>{selected.provider ? <BreadcrumbLink asChild><SessionLink run={run} selected={agent} onSelect={onSelect}>Braid agent session</SessionLink></BreadcrumbLink> : <BreadcrumbPage>Braid agent session</BreadcrumbPage>}</BreadcrumbItem>
      {selected.provider && <><BreadcrumbSeparator /><BreadcrumbItem><BreadcrumbPage>Provider session</BreadcrumbPage></BreadcrumbItem></>}
    </BreadcrumbList></Breadcrumb>
    <ActionButton className="session-back" icon={<ArrowLeft />} onClick={() => onSelect(selected.provider ? agent : item)}>{selected.provider ? '返回 agent session' : '返回工作项'}</ActionButton>
    <div className="detail-heading"><div className="detail-eyebrow">{selected.provider ? 'PROVIDER SESSION' : 'BRAID AGENT SESSION'}</div>
      <h2>{selected.provider ? provider?.native_session_id || selected.provider : [...new Set(records.map(record => record.profile_id))].join(' / ') || 'Braid agent session'}</h2>
      <CopyText className="session-identity">{selected.provider ? provider?.session_id || selected.provider : selected.agent}</CopyText>
    </div>
    <p className="session-coverage muted">{query.data?.some(record => record.source_mode === 'archive') ? '归档中的会话目录与历史。生命周期来自保存记录，缺失材料保留具体错误。' : coverage}</p>
    {query.error && <Notice tone="error" title="会话关系读取失败；缓存不能证明当前状态" description={<pre>{query.error.message}</pre>} />}
    {query.isPending ? <LoadingSkeleton rows={6} /> : !records.length || (selected.provider && !provider)
      ? <EmptyState description="登记数据源未保存或未发现此会话记录；缺失材料不等于从未执行" />
      : provider ? <>
        <Row gap={8} wrap><SessionState session={provider} /><StatusBadge>{provider.provider}</StatusBadge><StatusBadge>{provider.profile_id}</StatusBadge></Row>
        {provider.archive_native_error && <Notice tone="warning" title="归档原文不可定位" description={provider.archive_native_error} />}
        <Transcript key={`transcript-${provider.record_id}`} run={run} record={provider} />
        <details className="technical-details"><summary>会话身份与材料 <span className="muted">路径、revision 与来源</span></summary>
        <dl className="session-facts">{[
          { key: 'agent', label: 'Braid agent ID', children: <CopyText>{provider.group_id}</CopyText> },
          { key: 'record', label: 'Physical 记录 ID', children: provider.record_id },
          { key: 'native', label: 'Native session ID', children: provider.native_session_id || '未确认' },
          { key: 'parent', label: 'Parent native ID', children: provider.parent_native_session_id || '未记录' },
          { key: 'generation', label: 'Assignment generation', children: provider.assignment_generation ?? '未记录' },
          { key: 'revision', label: 'Context revision', children: provider.context_revision || '未记录' },
          { key: 'digest', label: 'Profile digest', children: provider.effective_profile_digest || '未记录' },
          { key: 'worktree', label: '工作树', children: provider.worktree || '未记录' },
          { key: 'context', label: 'Context 材料', children: provider.context_path },
          { key: 'instructions', label: 'Instructions 材料', children: provider.instructions_path },
          { key: 'path', label: '原生文件', children: provider.native_session_path || 'CLI 未提供' },
        ].map(fact => <div key={fact.key}><dt>{fact.label}</dt><dd>{fact.children}</dd></div>)}</dl>
        </details>
        <TurnHistory key={`turns-${provider.record_id}`} provider={provider} />
      </> : <>
        <dl className="session-facts">{[
          { key: 'item', label: '工作项', children: label }, { key: 'providers', label: '已发现 provider', children: `${records.length} 条，其中 ${records.filter(historical).length} 条历史` },
          { key: 'generation', label: 'Assignment generation', children: [...new Set(records.map(record => record.assignment_generation ?? '未记录'))].join(', ') },
        ].map(fact => <div key={fact.key}><dt>{fact.label}</dt><dd>{fact.children}</dd></div>)}</dl>
        <h4>Provider sessions · 包括历史</h4>
        <ProviderDirectory key={selected.agent} run={run} records={records} agent={agent} onSelect={onSelect} />
      </>}
  </section>;
}
