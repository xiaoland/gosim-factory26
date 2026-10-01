import { useEffect, useRef, useState } from 'react';
import { Alert, App as AntApp, Avatar, Badge, Button, Divider, Empty, Flex, Input, Modal, Select, Skeleton, Space, Spin, Tag, Tooltip, Typography } from 'antd';
import { BranchesOutlined, CheckCircleOutlined, CloseCircleOutlined, CodeOutlined, EditOutlined, EyeOutlined, ExclamationCircleOutlined, FileTextOutlined, LockOutlined, MessageOutlined, PauseCircleOutlined, PlayCircleOutlined, PullRequestOutlined, ReloadOutlined, SearchOutlined, SendOutlined, UnlockOutlined, UserOutlined } from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError, url, type Action, type ControlReceipt, type Item, type Kind, type Relation, type Run, type RuntimeState, type Selection, type WorkItem } from './api';
import { BodyInput, Markdown } from './Markdown';
import Discussion from './Discussion';
import Sessions, { SessionLinks } from './Sessions';
import { useNavigation } from './navigation';

const { Text, Title } = Typography;
type EditDraft = { title: string; body: string; revision: number };

function ItemIcon({ item }: { item: Pick<WorkItem, 'kind' | 'state'> }) {
  const closed = item.state !== 'OPEN';
  return <span className={`item-icon ${item.state === 'MERGED' ? 'merged' : closed ? 'closed' : 'open'}`}>
    {item.kind === 'pr' ? <PullRequestOutlined /> : closed ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
  </span>;
}

function StateTag({ state }: { state: string }) {
  return <Tag className="state-tag" color={state === 'OPEN' ? 'success' : state === 'MERGED' ? 'purple' : 'default'}>
    {state === 'OPEN' ? '开放' : state === 'MERGED' ? '已合并' : state === 'CLOSED' ? '已关闭' : state}
  </Tag>;
}

function ErrorAlert({ error, title, onClose }: { error: Error | null; title: string; onClose?: () => void }) {
  return error && <Alert className="error-alert" type="error" showIcon title={title}
    description={<pre>{error.message}</pre>} closable={!!onClose} onClose={onClose} />;
}

function RunControl({ run, busy, onBusy }: { run: Run; busy: boolean; onBusy: (busy: boolean) => void }) {
  const client = useQueryClient();
  const { message, modal } = AntApp.useApp();
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
      message.success(action === 'pause' ? run.writable ? '生成已暂停；人工输入仍可提交。' : '生成已暂停。' : '生成已恢复；将继续处理已入队输入。');
    },
    onSettled: () => { void client.invalidateQueries({ queryKey }); },
  });
  useEffect(() => { onBusy(mutation.isPending); }, [mutation.isPending, onBusy]);
  const runtime = query.error ? undefined : query.data;
  function resume() {
    modal.confirm({
      title: '恢复 ' + run.label + ' 的生成？',
      content: '恢复会继续该运行的全部 Agent 会话、Braid 定期检查，并处理暂停期间已入队的人工输入。',
      okText: '恢复生成', cancelText: '保持暂停',
      onOk: () => { mutation.mutate('resume'); },
    });
  }
  return <section className="run-control" aria-label="生成运行控制">
    <Flex justify="space-between" align="center" gap={12} wrap>
      <Space wrap>
        <Tag color={runtime?.paused ? 'orange' : runtime?.running ? 'green' : 'default'}
          icon={runtime?.paused ? <PauseCircleOutlined /> : <PlayCircleOutlined />}>
          {runtime ? runtime.paused ? '生成已暂停' : runtime.running ? '生成运行中' : '生成已停止 · ' + runtime.status : query.error ? '生成状态未确认' : '读取生成状态…'}
        </Tag>
        <Text type="secondary">{runtime?.paused ? run.writable ? '全部 Agent 会话和定期检查已冻结；人工编辑与评论保留。' : '全部 Agent 会话和定期检查已冻结。' : '暂停作用于当前运行的全部 Agent 会话和定期检查。'}</Text>
      </Space>
      {runtime?.running && <Button icon={runtime.paused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
        loading={mutation.isPending} disabled={busy || !!query.error}
        onClick={() => runtime.paused ? resume() : mutation.mutate('pause')}>{runtime.paused ? '恢复生成' : '暂停生成'}</Button>}
    </Flex>
    <ErrorAlert error={query.error} title="生成状态读取失败；上次状态不能作为控制结果" />
    <ErrorAlert error={mutation.error} title="运行控制未完成；核对实际状态与 journal" onClose={() => mutation.reset()} />
  </section>;
}

function Detail({ run, selected, writable, onSelect, onDirty, onBusy }: {
  run: string; selected: Selection; writable: boolean;
  onSelect: (selected: Selection) => void; onDirty: (dirty: boolean) => void; onBusy: (busy: boolean) => void;
}) {
  const client = useQueryClient();
  const { message } = AntApp.useApp();
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
      message.success({ content: <span className="cli-receipt">{result.result?.trim() || '操作完成'}</span>, duration: 8 });
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
    {query.isPending && <Skeleton active paragraph={{ rows: 9 }} />}</section>;
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
      <Flex justify="space-between" align="flex-start" gap={14}>
        <Title level={2}>{item.title} <span className="title-number">#{item.number}</span></Title>
        {writable && <Button icon={<EditOutlined />} disabled={busy || !!edit}
          onClick={() => setEdit({ title: item.title, body: item.body, revision: item.revision })}>编辑</Button>}
      </Flex>
      <Flex gap={10} wrap align="center"><StateTag state={item.state} /><Text type="secondary">revision {item.revision}</Text>
        <Text type="secondary">· {item.comments.length} 条评论</Text>
        {!writable && <Tag icon={<LockOutlined />}>只读运行</Tag>}
        {query.isFetching && <Spin size="small" />}
      </Flex>
      {item.kind === 'pr' && <div className="branch-info"><BranchesOutlined /> <code>{item.headRefName || item.head_ref || '未记录'}</code> → <code>{item.baseRefName || item.base_ref || '未记录'}</code>{item.draft && <Tag>Draft</Tag>}</div>}
    </div>
    <ErrorAlert error={query.error} title="刷新失败，仍显示上次成功读取的状态" />
    <ErrorAlert error={mutation.error} title="操作未完成，请核对状态与 journal 后再决定下一次操作" onClose={() => mutation.reset()} />
    <div className="detail-content">
      <div className="conversation">
        {edit && writable ? <section className="editor-card">
          <div className="section-label"><EditOutlined /> 编辑标题与正文 <Tag>基于 revision {edit.revision}</Tag></div>
          {changed && <Alert type="warning" showIcon title="对象已有新修订，当前草稿已保留。" description="保存仍使用开始编辑时的 revision；请先查看最新正文，再决定是否采用最新 revision。" />}
          <label className="field-label" htmlFor="item-title">标题</label>
          <Input id="item-title" value={edit.title} disabled={busy} onChange={event => setEdit({ ...edit, title: event.target.value })} />
          <label className="field-label">正文</label>
          <BodyInput label="编辑对象正文" value={edit.body} disabled={busy} onChange={body => setEdit({ ...edit, body })} />
          <Flex gap={8} wrap justify="space-between"><Space wrap>
            <Button type="primary" loading={busy} disabled={!edit.title.trim()} onClick={() => act({ action: 'edit', ...edit })}>保存修改</Button>
            <Button disabled={busy} onClick={() => setEdit(null)}>取消</Button>
          </Space><Button icon={<EyeOutlined />} onClick={() => setLatestOpen(true)}>查看最新正文</Button></Flex>
        </section> : <section className="body-card"><div className="section-label"><FileTextOutlined /> 正文</div><Markdown body={item.body} /></section>}
        <Flex className="discussion-title" justify="space-between" align="center">
          <Title level={4}><MessageOutlined /> 讨论 <Badge count={item.comments.length} color="#667085" /></Title>
          <Text type="secondary">隐藏正文与已解决历史按需展开</Text>
        </Flex>
        {item.comments.length ? <Discussion run={run} comments={item.comments} writable={writable} busy={busy} onReply={reply} onAction={act}
          onHide={id => { setHideReason(''); setHideComment(id); }} /> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无讨论" />}
        {writable && <section className="composer editor-card" ref={composer}>
          <Flex justify="space-between" align="center"><div className="section-label"><Avatar size={24} className="external-avatar" icon={<UserOutlined />} />
            {replyTo ? `回复评论 #${replyTo}` : '发表评论'}<Tag color="blue">external</Tag></div>
            {replyTo && <Button size="small" type="text" disabled={busy} onClick={() => setReplyTo(null)}>取消回复</Button>}
          </Flex>
          <BodyInput label="评论正文" value={comment} disabled={busy} onChange={setComment} />
          <Flex justify="space-between" align="center" gap={10} wrap><Text type="secondary">投递回执仅表示接收状态。</Text>
            <Button type="primary" icon={<SendOutlined />} loading={busy} disabled={!comment.trim()} onClick={() => act({ action: 'comment', body: comment, reply_to: replyTo })}>发表评论</Button></Flex>
        </section>}
      </div>
      <aside className="metadata">
        <SessionLinks run={run} selected={selected} onSelect={onSelect} />
        <div className="metadata-section"><div className="metadata-label"><UserOutlined /> 负责人</div>
          {item.assignees.length ? item.assignees.map(a => <div className="assignee" key={a.login}><Avatar size={24} icon={<UserOutlined />} /><strong>@{a.login}</strong></div>) : <Text type="secondary">未指派</Text>}
        </div>
        {relations.map(group => <div className="metadata-section" key={group.label}><div className="metadata-label">{group.label} <span>{group.values.length}</span></div>{group.values.map(value => relation(value, group.kind))}</div>)}
        {!!item.reason && <div className="metadata-section"><div className="metadata-label">关闭原因</div><div className="state-reason">{item.reason}</div></div>}
        <div className="metadata-section"><div className="metadata-label">访问权限</div><Tag color={writable ? 'blue' : 'default'} icon={writable ? <UnlockOutlined /> : <LockOutlined />}>{writable ? '可人工介入' : '只读'}</Tag></div>
        {writable && item.state !== 'MERGED' && <div className="metadata-section"><div className="metadata-label">生命周期</div>
          {item.state === 'OPEN' ? <Button danger icon={<CloseCircleOutlined />} disabled={busy} onClick={() => setClosing(true)}>关闭{item.kind === 'pr' ? ' PR' : ' Issue'}</Button>
            : <Button icon={<ReloadOutlined />} loading={busy} onClick={() => act({ action: 'reopen' })}>重新打开</Button>}
        </div>}
      </aside>
    </div>
    <Modal title={`隐藏评论 #${hideComment}`} open={hideComment != null && writable} onCancel={() => { if (!busy) { setHideComment(null); setHideReason(''); } }}
      okText="隐藏评论" cancelText="取消" confirmLoading={busy} okButtonProps={{ disabled: !hideReason.trim() }}
      onOk={() => act({ action: 'hide', comment: hideComment!, reason: hideReason })}>
      <p>隐藏保留原始评论；填写原因，便于以后理解此次处理。</p>
      <Input.TextArea autoSize={{ minRows: 3 }} aria-label="隐藏原因" value={hideReason} disabled={busy} onChange={event => setHideReason(event.target.value)} />
      <ErrorAlert error={mutation.error} title="隐藏失败" />
    </Modal>
    <Modal title={`关闭 ${item.kind === 'pr' ? 'PR' : 'Issue'} #${item.number}`} open={closing && writable}
      onCancel={() => { if (!busy) setClosing(false); }} okText="确认关闭" cancelText="取消" confirmLoading={busy}
      onOk={() => act({ action: 'close', ...(item.kind === 'issue' ? { reason: closeReason } : {}) })}>
      {item.kind === 'issue' ? <><p>选择此次关闭原因。</p><Select value={closeReason} onChange={setCloseReason} disabled={busy} style={{ width: '100%' }} options={[
        { value: 'completed', label: '已完成 · completed' }, { value: 'not planned', label: '不计划处理 · not planned' }, { value: 'duplicate', label: '重复 · duplicate' },
      ]} /></> : <p>确认关闭此 Pull request？关闭后可以重新打开。</p>}
      <ErrorAlert error={mutation.error} title="关闭失败" />
    </Modal>
    <Modal title={`最新正文 · revision ${item.revision}`} width={850} open={latestOpen} onCancel={() => setLatestOpen(false)}
      footer={<Space><Button onClick={() => setLatestOpen(false)}>返回草稿</Button>
        <Button type="primary" disabled={!changed || busy || !writable} onClick={() => { if (edit) setEdit({ ...edit, revision: item.revision }); setLatestOpen(false); mutation.reset(); }}>采用当前 revision，保留草稿</Button></Space>}>
      <Title level={3}>{item.title}</Title><Markdown body={item.body} />
    </Modal>
  </section>;
}

export default function App() {
  const { modal } = AntApp.useApp();
  const client = useQueryClient();
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('all');
  const [state, setState] = useState('all');
  const [assignee, setAssignee] = useState('all');
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [controlBusy, setControlBusy] = useState(false);
  const { run, selected, update } = useNavigation(dirty, busy || controlBusy, proceed => {
    modal.confirm({ title: '当前草稿尚未提交', content: '切换将丢弃当前标题、正文或评论草稿。', okText: '丢弃并切换', cancelText: '继续编辑', onOk: () => { setDirty(false); proceed(); } });
  });
  const runs = useQuery({ queryKey: ['runs'], queryFn: ({ signal }) => api<Run[]>('/api/runs', signal), refetchInterval: 5000 });
  const currentRun = runs.data?.find(r => r.id === run);
  const items = useQuery({ queryKey: ['items', run], queryFn: ({ signal }) => api<WorkItem[]>(url('/api/items', { run }), signal), enabled: !!currentRun, refetchInterval: 5000 });
  useEffect(() => {
    if (runs.data?.length && !run) update({ run: runs.data[0].id, selected }, true);
  }, [runs.data, run]);
  useEffect(() => {
    if (!selected && items.data?.length) update({ run, selected: { kind: items.data[0].kind, id: items.data[0].id } }, true);
  }, [items.data, selected]);
  useEffect(() => {
    function protect(event: BeforeUnloadEvent) { if (dirty || busy || controlBusy) { event.preventDefault(); event.returnValue = ''; } }
    window.addEventListener('beforeunload', protect);
    return () => window.removeEventListener('beforeunload', protect);
  }, [dirty, busy, controlBusy]);
  function choose(value: Selection) {
    if (value.kind === selected?.kind && value.id === selected.id && value.agent === selected.agent && value.provider === selected.provider) return;
    update({ run, selected: value });
  }
  const all = items.data || [];
  const needle = search.trim().toLowerCase();
  const filtered = all.filter(item => (kind === 'all' || item.kind === kind) && (state === 'all' || item.state === state)
    && (assignee === 'all' || (assignee === 'unassigned' ? !item.assignees.length : item.assignees.some(a => a.login === assignee)))
    && (!needle || `${item.title} #${item.number}`.toLowerCase().includes(needle)));
  const owners = [...new Set(all.flatMap(item => item.assignees.map(a => a.login)))].sort();
  return <div className="console-app">
    <header className="app-header">
      <a className="brand" href="/" onClick={event => event.preventDefault()}><span className="brand-mark"><BranchesOutlined /></span><strong>Braid</strong><span>Console</span></a>
      <Divider orientation="vertical" />
      <Select className="run-select" aria-label="选择运行" value={run || undefined} placeholder="选择运行" loading={runs.isPending} disabled={busy || controlBusy}
        onChange={value => { update({ run: value, selected: null }); setSearch(''); setAssignee('all'); }}
        options={runs.data?.map(r => ({ value: r.id, label: <Space><span>{r.label}</span><Tag color={r.writable ? 'blue' : 'default'}>{r.writable ? '可人工介入' : '只读'}</Tag></Space> }))} />
      <div className="header-status"><Badge status="processing" /><span>每 5 秒刷新</span><Tooltip title="立即读取列表、对象、会话与生成状态"><Button type="text" aria-label="刷新" icon={<ReloadOutlined />} onClick={() => { void items.refetch(); void runs.refetch(); void client.invalidateQueries({ queryKey: ['item', run] }); void client.invalidateQueries({ queryKey: ['sessions', run] }); void client.invalidateQueries({ queryKey: ['runtime', run] }); }} /></Tooltip></div>
    </header>
    <main className="workspace">
      <ErrorAlert error={runs.error} title="运行列表读取失败" />
      {!!run && runs.data && !currentRun && <Alert type="error" showIcon title="此运行未登记，请选择已登记的运行。" />}
      <div className="workspace-top"><Space><CodeOutlined /><Text strong>{currentRun?.mode === 'archive' ? '归档浏览' : '实时协作'}</Text><Text type="secondary">/</Text><Text>{currentRun?.label || '运行'}</Text></Space>
        <Tag icon={currentRun?.writable ? <UnlockOutlined /> : <LockOutlined />} color={currentRun?.writable ? 'blue' : 'default'}>{currentRun?.writable ? '人工介入' : '只读'}</Tag></div>
      <Alert className="context-note" type="info" showIcon title={currentRun?.writable ? '人工操作以 external 身份通过 Braid CLI 写入；投递回执不表示 Agent 已读取。' : '此运行仅供阅读；运行切换和内容展开均为只读操作。'} />
      {currentRun?.mode === 'archive' && <Alert className="context-note" type="warning" showIcon title="保存时的归档状态" description={currentRun.coverage.map((message, index) => <div key={index}>{message}</div>)} />}
      {currentRun?.controllable && <RunControl key={run} run={currentRun} busy={busy} onBusy={setControlBusy} />}
      <div className="workspace-layout">
        <aside className="item-panel">
          <div className="list-heading"><Flex justify="space-between" align="center"><Title level={4}>工作项</Title><Badge count={all.length} color="#667085" /></Flex>
            <Input prefix={<SearchOutlined />} aria-label="搜索标题或编号" placeholder="搜索标题或 #编号" allowClear value={search} onChange={event => setSearch(event.target.value)} />
            <div className="kind-tabs" role="group" aria-label="对象类型">
              {[{ value: 'all', label: '全部', count: all.length }, { value: 'issue', label: 'Issues', count: all.filter(i => i.kind === 'issue').length }, { value: 'pr', label: 'PRs', count: all.filter(i => i.kind === 'pr').length }].map(tab => <button key={tab.value} aria-pressed={kind === tab.value} className={kind === tab.value ? 'active' : ''} onClick={() => setKind(tab.value)}>{tab.label}<span>{tab.count}</span></button>)}
            </div>
            <Flex gap={8}><Select aria-label="状态筛选" value={state} onChange={setState} options={[{ value: 'all', label: '全部状态' }, { value: 'OPEN', label: '开放' }, { value: 'CLOSED', label: '已关闭' }, { value: 'MERGED', label: '已合并' }]} />
              <Select aria-label="负责人筛选" value={assignee} onChange={setAssignee} options={[{ value: 'all', label: '全部负责人' }, { value: 'unassigned', label: '未指派' }, ...owners.map(login => ({ value: login, label: `@${login}` }))]} /></Flex>
          </div>
          <ErrorAlert error={items.error} title="工作项读取失败" />
          <div className="item-list">
            {items.isPending ? <div className="list-loading"><Skeleton active paragraph={{ rows: 8 }} /></div> : filtered.length ? filtered.map(item => <button key={`${item.kind}-${item.id}`} className={`item-row ${selected?.kind === item.kind && selected.id === item.id ? 'selected' : ''}`} disabled={busy} onClick={() => choose({ kind: item.kind, id: item.id })}>
              <ItemIcon item={item} /><div className="item-summary"><div className="item-row-title">{item.title}</div>
                <div className="item-row-meta"><span>{item.kind === 'pr' ? 'PR' : 'Issue'} #{item.number}</span><StateTag state={item.state} /></div>
                <div className="item-owner"><UserOutlined /> {item.assignees.map(a => `@${a.login}`).join(', ') || '未指派'}</div>
              </div></button>) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={all.length ? '没有符合筛选条件的工作项' : '暂无工作项'} />}
          </div>
          <div className="list-footer"><span>{filtered.length} / {all.length} 个工作项</span>{items.isFetching ? <Spin size="small" /> : <span>{currentRun?.mode === 'archive' ? '保存状态只读' : 'CLI 实时读取'}</span>}</div>
        </aside>
        {selected && currentRun ? selected.agent ? <Sessions run={run} selected={selected} onSelect={choose} />
          : <Detail key={`${run}/${selected.kind}/${selected.id}`} run={run} selected={selected} writable={currentRun.writable} onSelect={choose} onDirty={setDirty} onBusy={setBusy} />
          : <section className="detail-panel detail-empty"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择一个 Issue 或 Pull request" /></section>}
      </div>
    </main>
  </div>;
}
