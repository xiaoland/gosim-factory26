import { ActionButton, CopyText, EmptyState, LoadingSkeleton, Notice, Row, StatusBadge } from '@/components/console-ui';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, url } from './http';
import { useState, type ReactNode } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { type ProviderSession, type ReviewView, type Selection } from './api';
import { routeURL } from './navigation';
import Transcript from './Transcript';
import FileBrowser from './FileBrowser';

const coverage = '展示登记 CLI 可枚举的当前与历史记录；缺失 physical 材料的会话可能未列出。生命周期来自 Braid 记录，实际执行状态以页面上方的生成状态为准。';
const historical = (session: ProviderSession) => ['replaced', 'retired'].includes(session.status);
export function useSessions(run: string) {
  return useQuery({ queryKey: ['sessions', run], queryFn: ({ signal }) => api<ProviderSession[]>(url('/api/sessions', { run }), signal),
    enabled: !!run, refetchInterval: 5000, retry: false });
}
export function useReview(run: string, selected: Selection) {
  return useQuery({ queryKey: ['review', run, selected.id, selected.review],
    queryFn: ({ signal }) => api<ReviewView>(url('/api/review', { run, pr: selected.id, id: selected.review! }), signal),
    enabled: !!selected.review, refetchInterval: 5000, retry: false });
}
export function SessionLink({ run, selected, onSelect, children }: { run: string; selected: Selection; onSelect: (value: Selection) => void; children: ReactNode }) {
  return <a href={routeURL(run, selected)} onClick={event => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); onSelect(selected);
  }}>{children}</a>;
}
function itemSessions(records: ProviderSession[], selected: Selection) {
  return records.filter(record => record.work_item_kind === (selected.review ? 'review' : selected.kind) && Number(record.work_item_id) === (selected.review || selected.id));
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
      return <div className="session-link" key={agent}><SessionLink run={run} selected={{ ...selected, agent }} onSelect={onSelect}>
        <strong>{[...new Set(providers.map(record => record.profile_id))].join(' / ')}</strong><code>{agent}</code>
      </SessionLink><span className="muted">{providers.length} 条 provider · {providers.filter(historical).length} 条历史</span></div>;
    }) : <span className="muted">未发现可枚举记录</span>}
    <p className="subtle">包括历史 provider；缺失 physical 材料的记录可能未列出。</p>
    {!!records.filter(record => !record.group_id).length && <span className="warning-text">存在未绑定 Braid agent 的记录。</span>}
  </div>;
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

function AgentFiles({ run, records, children }: { run: string; records: ProviderSession[]; children: ReactNode }) {
  const [view, setView] = useState('sessions');
  const [opened, setOpened] = useState(false);
  return <><Tabs className="session-transcript-tabs" value={view} onValueChange={value => { setView(value); if (value === 'files') setOpened(true); }}>
    <TabsList aria-label="Agent 会话内容"><TabsTrigger value="sessions">会话目录</TabsTrigger><TabsTrigger value="files">文件</TabsTrigger></TabsList>
  </Tabs><div hidden={view !== 'sessions'}>{children}</div>{opened && <div hidden={view !== 'files'}><FileBrowser run={run} records={records} /></div>}</>;
}

export default function Sessions({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useSessions(run);
  const review = useReview(run, selected);
  const records = itemSessions(selected.review && (!review.data || review.error) ? [] : query.data || [], selected).filter(record => record.group_id === selected.agent);
  const provider = selected.provider ? records.find(record => record.record_id === selected.provider) : undefined;
  const item = { kind: selected.kind, id: selected.id, review: selected.review };
  const agent = { ...item, agent: selected.agent };
  const label = selected.review ? `PR #${selected.id} · 审阅 #${selected.review}` : `${selected.kind === 'pr' ? 'PR' : 'Issue'} #${selected.id}`;
  return <section className="detail-panel session-panel">
    <Breadcrumb><BreadcrumbList>
      <BreadcrumbItem><BreadcrumbLink asChild><SessionLink run={run} selected={item} onSelect={onSelect}>{label}</SessionLink></BreadcrumbLink></BreadcrumbItem><BreadcrumbSeparator />
      <BreadcrumbItem>{selected.provider ? <BreadcrumbLink asChild><SessionLink run={run} selected={agent} onSelect={onSelect}>Braid agent session</SessionLink></BreadcrumbLink> : <BreadcrumbPage>Braid agent session</BreadcrumbPage>}</BreadcrumbItem>
      {selected.provider && <><BreadcrumbSeparator /><BreadcrumbItem><BreadcrumbPage>Provider session</BreadcrumbPage></BreadcrumbItem></>}
    </BreadcrumbList></Breadcrumb>
    <ActionButton className="session-back" icon={<ArrowLeft />} onClick={() => onSelect(selected.provider ? agent : item)}>{selected.provider ? '返回 agent session' : '返回工作项'}</ActionButton>
    <div className="detail-heading"><div className="detail-eyebrow">{selected.provider ? 'PROVIDER SESSION' : 'BRAID AGENT SESSION'}</div>
      <h2>{selected.provider ? provider ? `${provider.profile_id} 的会话` : 'Provider session' : [...new Set(records.map(record => record.profile_id))].join(' / ') || 'Braid agent session'}</h2>
    </div>
    <p className="session-coverage muted">{query.data?.some(record => record.source_mode === 'archive') ? '归档中的会话目录与历史。生命周期来自保存记录，缺失材料保留具体错误。' : coverage}</p>
    {query.error && <Notice tone="error" title="会话关系读取失败；缓存不能证明当前状态" description={<pre>{query.error.message}</pre>} />}
    {review.error && <Notice tone="error" title="审阅归属读取失败" description={<pre>{review.error.message}</pre>} />}
    {query.isPending || (selected.review && review.isPending) ? <LoadingSkeleton rows={6} /> : !records.length || (selected.provider && !provider)
      ? <EmptyState description="登记数据源未保存或未发现此会话记录；缺失材料不等于从未执行" />
      : provider ? <>
        <Row gap={8} wrap><SessionState session={provider} /><StatusBadge>{provider.provider}</StatusBadge><StatusBadge>{provider.profile_id}</StatusBadge></Row>
        {provider.archive_native_error && <Notice tone="warning" title="归档原文不可定位" description={provider.archive_native_error} />}
        <Transcript key={`transcript-${provider.record_id}`} run={run} record={provider} files={<FileBrowser run={run} records={[provider]} />} />
        <details className="technical-details"><summary>会话身份与材料 <span className="muted">路径、revision 与来源</span></summary>
        <dl className="session-facts">{[
          { key: 'agent', label: 'Braid agent ID', children: <CopyText>{provider.group_id}</CopyText> },
          { key: 'record', label: 'Physical 记录 ID', children: provider.record_id },
          { key: 'recovery', label: 'Provider 恢复身份', children: <CopyText>{provider.session_id}</CopyText> },
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
      </> : <AgentFiles key={selected.agent} run={run} records={records}>
        <details className="technical-details"><summary>Agent 身份</summary><CopyText className="session-identity">{selected.agent}</CopyText></details>
        <dl className="session-facts">{[
          { key: 'item', label: '工作项', children: label }, { key: 'providers', label: '已发现 provider', children: `${records.length} 条，其中 ${records.filter(historical).length} 条历史` },
          { key: 'generation', label: 'Assignment generation', children: [...new Set(records.map(record => record.assignment_generation ?? '未记录'))].join(', ') },
        ].map(fact => <div key={fact.key}><dt>{fact.label}</dt><dd>{fact.children}</dd></div>)}</dl>
        <h4>Provider sessions · 包括历史</h4>
        <ProviderDirectory key={selected.agent} run={run} records={records} agent={agent} onSelect={onSelect} />
      </AgentFiles>}
  </section>;
}
