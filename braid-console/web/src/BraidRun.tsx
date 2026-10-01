import { ActionButton, Choice, EditorDialog, EmptyState, LoadingSkeleton, Notice, Row, StatusBadge, UserAvatar } from '@/components/console-ui';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { Archive, LoaderCircle, SlidersHorizontal, X } from 'lucide-react';
import { api, ApiError, url } from './http';
import { useEffect, useRef, useState } from 'react';
import { GitBranch, CircleCheck, CircleX, Code2, Pencil, Eye, CircleDot, FileText, Lock, MessageSquare, CirclePause, CirclePlay, GitPullRequest, RotateCw, Search, Send, LockOpen, User } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { type Action, type ControlReceipt, type Item, type Kind, type Relation, type RuntimeState, type Selection, type WorkItem } from './api';
import { BodyInput, Markdown } from './Markdown';
import Discussion from './Discussion';
import Sessions, { SessionLinks } from './Sessions';
import type { RegisteredRun } from './runs';

type EditDraft = { title: string; body: string; revision: number };

function ItemIcon({ item }: { item: Pick<WorkItem, 'kind' | 'state'> }) {
  const closed = item.state !== 'OPEN';
  return <span className={`item-icon ${item.state === 'MERGED' ? 'merged' : closed ? 'closed' : 'open'}`}>
    {item.kind === 'pr' ? <GitPullRequest /> : closed ? <CircleCheck /> : <CircleDot />}
  </span>;
}

function StateTag({ state }: { state: string }) {
  return <StatusBadge className="state-tag" tone={state === 'OPEN' ? 'success' : state === 'MERGED' ? 'purple' : 'default'}>
    {state === 'OPEN' ? '开放' : state === 'MERGED' ? '已合并' : state === 'CLOSED' ? '已关闭' : state}
  </StatusBadge>;
}

function ErrorAlert({ error, title, onClose }: { error: Error | null; title: string; onClose?: () => void }) {
  return error && <Notice className="error-alert" tone="error" title={title}
    description={<pre>{error.message}</pre>} onClose={onClose} />;
}

function RunControl({ run, busy, onBusy }: { run: RegisteredRun; busy: boolean; onBusy: (busy: boolean) => void }) {
  const client = useQueryClient();
  const [confirmResume, setConfirmResume] = useState(false);
  const queryKey = ['runtime', run.id];
  const query = useQuery({
    queryKey, queryFn: ({ signal }) => api<RuntimeState>(url('/api/runtime', { run: run.id }), signal),
    refetchInterval: 5000, retry: false,
  });
  const mutation = useMutation({
    retry: false,
    mutationFn: (action: 'pause' | 'resume') => api<ControlReceipt>('/api/control', undefined, { run: run.id, action }),
    onSuccess: (receipt, action) => {
      client.setQueryData(queryKey, receipt.runtime);
      toast.success(action === 'pause' ? run.writable ? '生成已暂停；人工输入仍可提交。' : '生成已暂停。' : '生成已恢复；将继续处理已入队输入。');
    },
    onSettled: () => { void client.invalidateQueries({ queryKey }); },
  });
  useEffect(() => { onBusy(mutation.isPending); }, [mutation.isPending, onBusy]);
  const runtime = query.error ? undefined : query.data;
  return <section className="run-control" aria-label="生成运行控制">
    <Row justify="space-between" align="center" gap={12} wrap>
      <Row align="center" wrap>
        <StatusBadge tone={runtime?.paused ? 'orange' : runtime?.running ? 'green' : 'default'}
          icon={runtime?.paused ? <CirclePause /> : <CirclePlay />}>
          {runtime ? runtime.paused ? '生成已暂停' : runtime.running ? '生成运行中' : '生成已停止 · ' + runtime.status : query.error ? '生成状态未确认' : '读取生成状态…'}
        </StatusBadge>
        <span className="muted">{runtime?.paused ? run.writable ? '全部 Agent 会话和定期检查已冻结；人工编辑与评论保留。' : '全部 Agent 会话和定期检查已冻结。' : '暂停作用于当前运行的全部 Agent 会话和定期检查。'}</span>
      </Row>
      {runtime?.running && <ActionButton icon={runtime.paused ? <CirclePlay /> : <CirclePause />}
        pending={mutation.isPending} disabled={busy || !!query.error}
        onClick={() => runtime.paused ? setConfirmResume(true) : mutation.mutate('pause')}>{runtime.paused ? '恢复生成' : '暂停生成'}</ActionButton>}
    </Row>
    <ErrorAlert error={query.error} title="生成状态读取失败；上次状态不能作为控制结果" />
    <ErrorAlert error={mutation.error} title="运行控制未完成；核对实际状态与 journal" onClose={() => mutation.reset()} />
    <AlertDialog open={confirmResume} onOpenChange={setConfirmResume}><AlertDialogContent>
      <AlertDialogHeader><AlertDialogTitle>恢复 {run.label} 的生成？</AlertDialogTitle><AlertDialogDescription>恢复会继续该运行的全部 Agent 会话、Braid 定期检查，并处理暂停期间已入队的人工输入。</AlertDialogDescription></AlertDialogHeader>
      <AlertDialogFooter><AlertDialogCancel>保持暂停</AlertDialogCancel><AlertDialogAction disabled={busy || mutation.isPending || !runtime?.running || !runtime.paused || !!query.error} onClick={() => mutation.mutate('resume')}>恢复生成</AlertDialogAction></AlertDialogFooter>
    </AlertDialogContent></AlertDialog>
  </section>;
}

function Detail({ run, selected, writable, onSelect, onDirty, onBusy }: {
  run: string; selected: Selection; writable: boolean;
  onSelect: (selected: Selection) => void; onDirty: (dirty: boolean) => void; onBusy: (busy: boolean) => void;
}) {
  const client = useQueryClient();
  const [edit, setEdit] = useState<EditDraft | null>(null);
  const [comment, setComment] = useState('');
  const [replyTo, setReplyTo] = useState<number | null>(null);
  const [hideComment, setHideComment] = useState<number | null>(null);
  const [hideReason, setHideReason] = useState('');
  const [closing, setClosing] = useState(false);
  const [closeReason, setCloseReason] = useState('completed');
  const [latestOpen, setLatestOpen] = useState(false);
  const composer = useRef<HTMLDivElement>(null);
  const queryKey = ['item', run, selected.kind, selected.id];
  const query = useQuery({
    queryKey, queryFn: ({ signal }) => api<Item>(url('/api/item', { run, ...selected }), signal),
    refetchInterval: 5000,
  });
  const mutation = useMutation({
    retry: false,
    mutationFn: (action: Action) => {
      if (!writable) throw new Error('当前运行只读。');
      return api<{ result: string }>('/api/action', undefined, { run, ...selected, ...action });
    },
    onSuccess: (result, action) => {
      if (action.action === 'edit') setEdit(null);
      if (action.action === 'comment') { setComment(''); setReplyTo(null); }
      if (action.action === 'hide') { setHideComment(null); setHideReason(''); }
      if (action.action === 'close') setClosing(false);
      toast.success(<span className="cli-receipt">{result.result?.trim() || '操作完成'}</span>, { duration: 8000 });
      void client.invalidateQueries({ queryKey });
      void client.invalidateQueries({ queryKey: ['items', run] });
      void client.invalidateQueries({ queryKey: ['thread', run] });
      void client.invalidateQueries({ queryKey: ['comment', run] });
    },
    onError: error => {
      if (error instanceof ApiError && error.status === 409) void client.invalidateQueries({ queryKey });
    },
  });
  useEffect(() => { onDirty(!!edit || !!comment || !!hideReason); }, [edit, comment, hideReason, onDirty]);
  useEffect(() => { onBusy(mutation.isPending); }, [mutation.isPending, onBusy]);
  const item = query.data;
  const busy = mutation.isPending;
  function act(action: Action) { if (!busy && writable) mutation.mutate(action); }
  function reply(id: number) {
    setReplyTo(id);
    composer.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    composer.current?.querySelector('textarea')?.focus();
  }
  function relation(value: Relation, defaultKind: Kind) {
    const kind = value.kind === 'pull_request' || value.kind === 'pr' ? 'pr' : value.kind === 'issue' ? 'issue' : defaultKind;
    return <button className="relation-link" key={`${kind}-${value.number}`} disabled={busy}
      onClick={() => onSelect({ kind, id: value.number })}>
      <ItemIcon item={{ kind, state: value.state || 'OPEN' }} />
      <span><strong>{kind === 'pr' ? 'PR' : 'Issue'} #{value.number}</strong><span>{value.title}</span></span>
    </button>;
  }
  if (!item) return <section className="detail-panel"><ErrorAlert error={query.error} title="对象读取失败" />
    {query.isPending && <LoadingSkeleton rows={9} />}</section>;
  const changed = edit && edit.revision !== item.revision;
  const relations = [
    { label: '父 Issue', values: item.parent_issue ? [item.parent_issue] : [], kind: 'issue' as Kind },
    { label: '子 Issue', values: item.sub_issues || [], kind: 'issue' as Kind },
    { label: '关联 PR', values: item.associated_prs || [], kind: 'pr' as Kind },
    { label: '关联 Issue', values: item.associated_issues || [], kind: 'issue' as Kind },
  ].filter(group => group.values.length);
  return <section className="detail-panel">
    <div className="detail-heading">
      <div className="detail-eyebrow">{item.kind === 'issue' ? 'ISSUE' : 'PULL REQUEST'} <span>#{item.number}</span></div>
      <Row justify="space-between" align="flex-start" gap={14}>
        <h2>{item.title} <span className="title-number">#{item.number}</span></h2>
        {writable && <ActionButton icon={<Pencil />} disabled={busy || !!edit}
          onClick={() => setEdit({ title: item.title, body: item.body, revision: item.revision })}>编辑</ActionButton>}
      </Row>
      <Row gap={10} wrap align="center"><StateTag state={item.state} /><span className="muted">revision {item.revision}</span>
        <span className="muted">· {item.comments.length} 条评论</span>
        {!writable && <StatusBadge icon={<Lock />}>只读运行</StatusBadge>}
        {query.isFetching && <LoaderCircle className="size-4 animate-spin" aria-label="正在刷新" />}
      </Row>
      {item.kind === 'pr' && <div className="branch-info"><GitBranch /> <code>{item.headRefName || item.head_ref || '未记录'}</code> → <code>{item.baseRefName || item.base_ref || '未记录'}</code>{item.draft && <StatusBadge>Draft</StatusBadge>}</div>}
    </div>
    <ErrorAlert error={query.error} title="刷新失败，仍显示上次成功读取的状态" />
    <ErrorAlert error={mutation.error} title="操作未完成，请核对状态与 journal 后再决定下一次操作" onClose={() => mutation.reset()} />
    <div className="detail-content">
      <div className="conversation">
        {edit && writable ? <section className="editor-card">
          <div className="section-label"><Pencil /> 编辑标题与正文 <StatusBadge>基于 revision {edit.revision}</StatusBadge></div>
          {changed && <Notice tone="warning" title="对象已有新修订，当前草稿已保留。" description="保存仍使用开始编辑时的 revision；请先查看最新正文，再决定是否采用最新 revision。" />}
          <label className="field-label" htmlFor="item-title">标题</label>
          <Input id="item-title" value={edit.title} disabled={busy} onChange={event => setEdit({ ...edit, title: event.target.value })} />
          <label className="field-label">正文</label>
          <BodyInput label="编辑对象正文" value={edit.body} disabled={busy} onChange={body => setEdit({ ...edit, body })} />
          <Row gap={8} wrap justify="space-between"><Row align="center" wrap>
            <ActionButton variant="default" pending={busy} disabled={!edit.title.trim()} onClick={() => act({ action: 'edit', ...edit })}>保存修改</ActionButton>
            <ActionButton disabled={busy} onClick={() => setEdit(null)}>取消</ActionButton>
          </Row><ActionButton icon={<Eye />} onClick={() => setLatestOpen(true)}>查看最新正文</ActionButton></Row>
        </section> : <section className="body-card"><div className="section-label"><FileText /> 正文</div><Markdown body={item.body} /></section>}
        <Row className="discussion-title" justify="space-between" align="center">
          <h4><MessageSquare /> 讨论 <StatusBadge>{item.comments.length}</StatusBadge></h4>
          <span className="muted">隐藏正文与已解决历史按需展开</span>
        </Row>
        {item.comments.length ? <Discussion run={run} comments={item.comments} writable={writable} busy={busy} onReply={reply} onAction={act}
          onHide={id => { setHideReason(''); setHideComment(id); }} /> : <EmptyState description="暂无讨论" />}
        {writable && <section className="composer editor-card" ref={composer}>
          <Row justify="space-between" align="center"><div className="section-label"><UserAvatar size={24} className="external-avatar" />
            {replyTo ? `回复评论 #${replyTo}` : '发表评论'}<StatusBadge tone="blue">external</StatusBadge></div>
            {replyTo && <ActionButton size="sm" variant="ghost" disabled={busy} onClick={() => setReplyTo(null)}>取消回复</ActionButton>}
          </Row>
          <BodyInput label="评论正文" value={comment} disabled={busy} onChange={setComment} />
          <Row justify="space-between" align="center" gap={10} wrap><span className="muted">投递回执仅表示接收状态。</span>
            <ActionButton variant="default" icon={<Send />} pending={busy} disabled={!comment.trim()} onClick={() => act({ action: 'comment', body: comment, reply_to: replyTo })}>发表评论</ActionButton></Row>
        </section>}
      </div>
      <aside className="metadata">
        <SessionLinks run={run} selected={selected} onSelect={onSelect} />
        <div className="metadata-section"><div className="metadata-label"><User /> 负责人</div>
          {item.assignees.length ? item.assignees.map(a => <div className="assignee" key={a.login}><UserAvatar size={24} /><strong>@{a.login}</strong></div>) : <span className="muted">未指派</span>}
        </div>
        {relations.map(group => <div className="metadata-section" key={group.label}><div className="metadata-label">{group.label} <span>{group.values.length}</span></div>{group.values.map(value => relation(value, group.kind))}</div>)}
        {!!item.reason && <div className="metadata-section"><div className="metadata-label">关闭原因</div><div className="state-reason">{item.reason}</div></div>}
        <div className="metadata-section"><div className="metadata-label">访问权限</div><StatusBadge tone={writable ? 'blue' : 'default'} icon={writable ? <LockOpen /> : <Lock />}>{writable ? '可人工介入' : '只读'}</StatusBadge></div>
        {writable && item.state !== 'MERGED' && <div className="metadata-section"><div className="metadata-label">生命周期</div>
          {item.state === 'OPEN' ? <ActionButton variant="destructive" icon={<CircleX />} disabled={busy} onClick={() => setClosing(true)}>关闭{item.kind === 'pr' ? ' PR' : ' Issue'}</ActionButton>
            : <ActionButton icon={<RotateCw />} pending={busy} onClick={() => act({ action: 'reopen' })}>重新打开</ActionButton>}
        </div>}
      </aside>
    </div>
    <EditorDialog title={`隐藏评论 #${hideComment}`} description="隐藏保留原始评论；填写原因，便于以后理解此次处理。" open={hideComment != null && writable} busy={busy} onClose={() => { setHideComment(null); setHideReason(''); }}
      footer={<><ActionButton disabled={busy} onClick={() => { setHideComment(null); setHideReason(''); }}>取消</ActionButton><ActionButton variant="default" pending={busy} disabled={!hideReason.trim()} onClick={() => act({ action: 'hide', comment: hideComment!, reason: hideReason })}>隐藏评论</ActionButton></>}>
      <Textarea rows={3} aria-label="隐藏原因" value={hideReason} disabled={busy} onChange={event => setHideReason(event.target.value)} />
      <ErrorAlert error={mutation.error} title="隐藏失败" />
    </EditorDialog>
    <EditorDialog title={`关闭 ${item.kind === 'pr' ? 'PR' : 'Issue'} #${item.number}`} description={item.kind === 'issue' ? '选择此次关闭原因。' : '确认关闭此 Pull request？关闭后可以重新打开。'} open={closing && writable} busy={busy}
      onClose={() => setClosing(false)} footer={<><ActionButton disabled={busy} onClick={() => setClosing(false)}>取消</ActionButton><ActionButton variant="destructive" pending={busy} onClick={() => act({ action: 'close', ...(item.kind === 'issue' ? { reason: closeReason } : {}) })}>确认关闭</ActionButton></>}>
      {item.kind === 'issue' && <Choice label="关闭原因" value={closeReason} onChange={setCloseReason} disabled={busy} options={[
        { value: 'completed', label: '已完成 · completed' }, { value: 'not planned', label: '不计划处理 · not planned' }, { value: 'duplicate', label: '重复 · duplicate' },
      ]} />}
      <ErrorAlert error={mutation.error} title="关闭失败" />
    </EditorDialog>
    <EditorDialog title={`最新正文 · revision ${item.revision}`} description="核对最新正文后，可以采用当前 revision 并保留已有草稿。" wide open={latestOpen} onClose={() => setLatestOpen(false)}
      footer={<Row align="center"><ActionButton onClick={() => setLatestOpen(false)}>返回草稿</ActionButton>
        <ActionButton variant="default" disabled={!changed || busy || !writable} onClick={() => { if (edit) setEdit({ ...edit, revision: item.revision }); setLatestOpen(false); mutation.reset(); }}>采用当前 revision，保留草稿</ActionButton></Row>}>
      <h3>{item.title}</h3><Markdown body={item.body} />
    </EditorDialog>
  </section>;
}

export default function BraidRun({ currentRun, selected, onSelect, onDirty, onBusy }: {
  currentRun: RegisteredRun; selected: Selection | null;
  onSelect: (selected: Selection, replace?: boolean) => void;
  onDirty: (dirty: boolean) => void; onBusy: (busy: boolean) => void;
}) {
  const run = currentRun.id;
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('all');
  const [state, setState] = useState('all');
  const [assignee, setAssignee] = useState('all');
  const [busy, setBusy] = useState(false);
  const [controlBusy, setControlBusy] = useState(false);
  const items = useQuery({ queryKey: ['items', run], queryFn: ({ signal }) => api<WorkItem[]>(url('/api/items', { run }), signal), refetchInterval: 5000, retry: false });
  useEffect(() => { onBusy(busy || controlBusy); }, [busy, controlBusy, onBusy]);
  useEffect(() => () => { onDirty(false); onBusy(false); }, [onDirty, onBusy]);
  useEffect(() => {
    if (!selected && items.data?.length) onSelect({ kind: items.data[0].kind, id: items.data[0].id }, true);
  }, [items.data, selected]);
  function choose(value: Selection) {
    if (value.kind === selected?.kind && value.id === selected.id && value.agent === selected.agent && value.provider === selected.provider) return;
    onSelect(value);
  }
  const all = items.data || [];
  const needle = search.trim().toLowerCase();
  const filtered = all.filter(item => (kind === 'all' || item.kind === kind) && (state === 'all' || item.state === state)
    && (assignee === 'all' || (assignee === 'unassigned' ? !item.assignees.length : item.assignees.some(a => a.login === assignee)))
    && (!needle || `${item.title} #${item.number}`.toLowerCase().includes(needle)));
  const owners = [...new Set(all.flatMap(item => item.assignees.map(a => a.login)))].sort();
  const filtering = !!needle || kind !== 'all' || state !== 'all' || assignee !== 'all';
  function resetFilters() { setSearch(''); setKind('all'); setState('all'); setAssignee('all'); }
  return <>
      <div className="workspace-top"><Row align="center"><Code2 /><span className="font-semibold">{currentRun.mode === 'archive' ? '归档浏览' : '实时协作'}</span><span className="muted">/</span><span>{currentRun.label || '运行'}</span></Row>
        <StatusBadge icon={currentRun.writable ? <LockOpen /> : <Lock />} tone={currentRun.writable ? 'blue' : 'default'}>{currentRun.writable ? '人工介入' : '只读'}</StatusBadge></div>
      {currentRun.writable && <Notice className="context-note" tone="info" title="人工操作以 external 身份通过 Braid CLI 写入；投递回执不表示 Agent 已读取。" />}
      {currentRun.mode === 'archive' && <details className="archive-note"><summary><Archive size={15} aria-hidden="true" /><span>保存状态只读</span><span className="muted">查看保存范围与材料缺口</span></summary>
        <div>{currentRun.coverage.map((message, index) => <p key={index}>{message}</p>)}</div></details>}
      {currentRun.controllable && <RunControl key={run} run={currentRun} busy={busy} onBusy={setControlBusy} />}
      <div className="workspace-layout">
        <aside className="item-panel">
          <div className="list-heading"><Row justify="space-between" align="center"><h4>工作项 <StatusBadge>{all.length}</StatusBadge></h4>{filtering && <ActionButton size="xs" variant="ghost" onClick={resetFilters}>清除筛选</ActionButton>}</Row>
            <div className="search-field"><Search size={16} aria-hidden="true" /><Input aria-label="搜索标题或编号" placeholder="搜索标题或 #编号" value={search} onChange={event => setSearch(event.target.value)} />
              {search && <ActionButton className="search-clear" variant="ghost" size="icon-xs" aria-label="清除搜索" icon={<X />} onClick={() => setSearch('')} />}</div>
            <Tabs className="kind-tabs" value={kind} onValueChange={setKind}><TabsList className="w-full" aria-label="对象类型">
              {[{ value: 'all', label: '全部', count: all.length }, { value: 'issue', label: 'Issues', count: all.filter(i => i.kind === 'issue').length }, { value: 'pr', label: 'PRs', count: all.filter(i => i.kind === 'pr').length }].map(tab => <TabsTrigger className="flex-1" key={tab.value} value={tab.value} aria-label={tab.label}>{tab.label}<span>{tab.count}</span></TabsTrigger>)}
            </TabsList></Tabs>
            <Row gap={8}><Choice label="状态筛选" value={state} onChange={setState} options={[{ value: 'all', label: '全部状态' }, { value: 'OPEN', label: '开放' }, { value: 'CLOSED', label: '已关闭' }, { value: 'MERGED', label: '已合并' }]} />
              <Choice label="负责人筛选" value={assignee} onChange={setAssignee} options={[{ value: 'all', label: '全部负责人' }, { value: 'unassigned', label: '未指派' }, ...owners.map(login => ({ value: login, label: `@${login}` }))]} /></Row>
          </div>
          <ErrorAlert error={items.error} title="工作项读取失败" />
          <div className="item-list">
            {items.isPending ? <div className="list-loading"><LoadingSkeleton rows={8} /></div> : filtered.length ? filtered.map(item => <button key={`${item.kind}-${item.id}`} className={`item-row ${selected?.kind === item.kind && selected.id === item.id ? 'selected' : ''}`} disabled={busy} onClick={() => choose({ kind: item.kind, id: item.id })}>
              <ItemIcon item={item} /><div className="item-summary"><div className="item-row-title">{item.title}</div>
                <div className="item-row-meta"><span>{item.kind === 'pr' ? 'PR' : 'Issue'} #{item.number}</span><StateTag state={item.state} /></div>
                <div className="item-owner"><User /> {item.assignees.map(a => `@${a.login}`).join(', ') || '未指派'}</div>
              </div></button>) : <div><EmptyState description={items.error ? '未取得工作项；请查看读取错误' : all.length ? '没有符合筛选条件的工作项' : '暂无工作项'} />
                {filtering && <ActionButton className="empty-reset" icon={<SlidersHorizontal />} onClick={resetFilters}>清除筛选，查看全部</ActionButton>}</div>}
          </div>
          <div className="list-footer"><span>{filtered.length} / {all.length} 个工作项</span>{items.isFetching ? <LoaderCircle className="size-4 animate-spin" aria-label="正在刷新" /> : <span>{currentRun.mode === 'archive' ? '保存状态只读' : 'CLI 实时读取'}</span>}</div>
        </aside>
        {selected ? selected.agent ? <Sessions run={run} selected={selected} onSelect={choose} />
          : <Detail key={`${run}/${selected.kind}/${selected.id}`} run={run} selected={selected} writable={currentRun.writable} onSelect={choose} onDirty={onDirty} onBusy={setBusy} />
          : <section className="detail-panel detail-empty"><EmptyState description="选择一个 Issue 或 Pull request" /></section>}
      </div>
  </>;
}
