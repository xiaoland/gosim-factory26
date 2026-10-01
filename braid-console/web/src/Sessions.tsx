import { api, url } from './http';
import type { ReactNode } from 'react';
import { Alert, Breadcrumb, Button, Descriptions, Empty, Flex, Skeleton, Space, Table, Tag, Typography } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { type NativeEntry, type ProviderSession, type Selection, type TranscriptPage } from './api';
import { routeURL } from './navigation';
import { Markdown } from './Markdown';

const { Text, Title } = Typography;
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
  return <Space size={4} wrap>{historical(session) && <Tag>历史</Tag>}<Tag>{session.status}</Tag></Space>;
}
export function SessionLinks({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useSessions(run);
  const records = itemSessions(query.data || [], selected);
  const groups = [...new Set(records.map(record => record.group_id).filter((id): id is string => !!id))];
  return <div className="metadata-section session-links"><div className="metadata-label">Braid agent sessions <span>{groups.length}</span></div>
    {query.error && <Alert type="error" title="会话关系读取失败" description={<pre>{query.error.message}</pre>} />}
    {query.isPending ? <Skeleton active paragraph={{ rows: 2 }} /> : groups.length ? groups.map(agent => {
      const providers = records.filter(record => record.group_id === agent);
      return <div className="session-link" key={agent}><SessionLink run={run} selected={{ kind: selected.kind, id: selected.id, agent }} onSelect={onSelect}>
        <strong>{[...new Set(providers.map(record => record.profile_id))].join(' / ')}</strong><code>{agent}</code>
      </SessionLink><Text type="secondary">{providers.length} 条 provider · {providers.filter(historical).length} 条历史</Text></div>;
    }) : <Text type="secondary">未发现可枚举记录</Text>}
    <p className="subtle">包括历史 provider；缺失 physical 材料的记录可能未列出。</p>
    {!!records.filter(record => !record.group_id).length && <Text type="warning">存在未绑定 Braid agent 的记录。</Text>}
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
  if (entry.error) return <Alert type="error" title={`JSONL 字节 ${entry.offset} 解析失败`} description={<><pre>{entry.error}</pre><pre className="native-code">{entry.raw}</pre></>} />;
  const value = entry.value || {};
  const payload = object(value.message) || (value.type === 'response_item' ? object(value.payload) : null);
  const role = payload?.role;
  const content = payload?.content;
  const tool = role === 'toolResult' || payload?.type === 'function_call_output';
  if (payload && (role || payload.type === 'function_call' || tool)) return <article className={`native-entry ${tool ? 'native-result' : ''} ${payload.isError ? 'native-failed' : ''}`}>
    <Flex className="native-entry-head" gap={8} wrap><Tag color={tool ? payload.isError ? 'error' : 'cyan' : role === 'user' ? 'blue' : 'green'}>
      {tool ? '工具结果' : role === 'user' ? '用户' : role === 'assistant' ? 'Agent' : '工具调用'}</Tag>
      {tool && <strong>{String(payload.toolName || payload.name || '')}</strong>}
      {!!(payload.toolCallId || payload.call_id) && <code>{String(payload.toolCallId || payload.call_id)}</code>}
      {!!payload.isError && <Tag color="error">isError=true</Tag>}
      <Text type="secondary">{String(value.timestamp || payload.timestamp || '')} · 字节 {entry.offset}</Text>
    </Flex>
    <div className="native-entry-body">{Array.isArray(content) ? content.map((block, index) => tool
      ? <pre className="native-code" key={index}>{String(object(block)?.text ?? json(block))}</pre>
      : <NativeBlock key={index} value={block} />) : content ? <NativeBlock value={content} /> : payload.type === 'function_call' ? <NativeBlock value={payload} />
      : <pre className="native-code">{typeof payload.output === 'string' ? payload.output : json(payload)}</pre>}
      {!!(payload.errorMessage || payload.error) && <Alert type="error" title="原生错误" description={<pre>{String(payload.errorMessage || json(payload.error))}</pre>} />}
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
    <Flex align="center" justify="space-between" gap={12} wrap><Title level={4}>原生对话与工具调用</Title>
      <Button icon={<ReloadOutlined />} loading={query.isFetching} onClick={() => { void query.refetch(); }}>刷新已加载记录</Button></Flex>
    <Text type="secondary">按文件位置分批读取；工具参数、结果和错误保留原始内容，凭据字段脱敏。</Text>
    {query.error && <Alert className="error-alert" type="error" showIcon title="原生文件读取失败；会话元数据仍可查看" description={<pre>{query.error.message}</pre>} />}
    {query.isPending && <Skeleton active paragraph={{ rows: 6 }} />}
    {entries.map(entry => <NativeRecord key={entry.offset} entry={entry} />)}
    {!query.isPending && !query.error && !entries.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={last?.waiting ? '文件末尾记录尚未写完整，请稍后刷新' : '原生文件没有记录'} />}
    {last && <Flex className="native-pagination" gap={12} align="center" wrap><Text type="secondary">已加载 {entries.length} 条记录 · 字节 {last.next_offset} / {last.size}{last.eof ? ' · 已到当前文件末尾' : ''}</Text>
      {query.hasNextPage && <Button loading={query.isFetchingNextPage} onClick={() => { void query.fetchNextPage(); }}>{last.waiting ? '重新读取未完成的末尾' : '加载后续记录'}</Button>}
    </Flex>}
  </section>;
}

export default function Sessions({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useSessions(run);
  const records = itemSessions(query.data || [], selected).filter(record => record.group_id === selected.agent);
  const provider = selected.provider ? records.find(record => record.record_id === selected.provider) : undefined;
  const item = { kind: selected.kind, id: selected.id };
  const agent = { ...item, agent: selected.agent };
  const label = `${selected.kind === 'pr' ? 'PR' : 'Issue'} #${selected.id}`;
  return <section className="detail-panel session-panel">
    <Breadcrumb items={[{ title: <SessionLink run={run} selected={item} onSelect={onSelect}>{label}</SessionLink> },
      { title: selected.provider ? <SessionLink run={run} selected={agent} onSelect={onSelect}>Braid agent session</SessionLink> : 'Braid agent session' },
      ...(selected.provider ? [{ title: 'Provider session' }] : [])]} />
    <Button className="session-back" icon={<ArrowLeftOutlined />} onClick={() => onSelect(selected.provider ? agent : item)}>{selected.provider ? '返回 agent session' : '返回工作项'}</Button>
    <div className="detail-heading"><div className="detail-eyebrow">{selected.provider ? 'PROVIDER SESSION' : 'BRAID AGENT SESSION'}</div>
      <Title level={2}>{selected.provider ? provider?.native_session_id || selected.provider : [...new Set(records.map(record => record.profile_id))].join(' / ') || 'Braid agent session'}</Title>
      <Text copyable className="session-identity">{selected.provider ? provider?.session_id || selected.provider : selected.agent}</Text>
    </div>
    <Alert className="context-note" type="info" showIcon title={query.data?.some(record => record.source_mode === 'archive') ? '展示归档保存时的 physical 会话目录；历史生命周期不代表当前执行状态，缺失材料保持明确缺口。' : coverage} />
    {query.error && <Alert type="error" title="会话关系读取失败；缓存不能证明当前状态" description={<pre>{query.error.message}</pre>} />}
    {query.isPending ? <Skeleton active paragraph={{ rows: 6 }} /> : !records.length || (selected.provider && !provider)
      ? <Empty description="登记数据源未保存或未发现此会话记录；缺失材料不等于从未执行" />
      : provider ? <>
        <Flex gap={8} wrap><SessionState session={provider} /><Tag>{provider.provider}</Tag><Tag>{provider.profile_id}</Tag></Flex>
        {provider.archive_native_error && <Alert type="warning" showIcon title="归档原文不可定位" description={provider.archive_native_error} />}
        <Descriptions className="session-facts" size="small" column={1} bordered items={[
          { key: 'agent', label: 'Braid agent ID', children: <Text copyable>{provider.group_id}</Text> },
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
        ]} />
        <Title level={4}>Turn 历史 <Text type="secondary">{provider.source_mode === 'archive' && !provider.turns ? '未保存' : `${provider.turns?.length || 0} 条`}</Text></Title>
        <Table size="small" rowKey="braid_turn_id" pagination={false} scroll={{ x: 650 }} dataSource={provider.turns || []} columns={[
          { title: 'Braid turn / Provider turn', dataIndex: 'braid_turn_id', render: (id, turn) => <><code>{id}</code><div className="subtle">{turn.provider_turn_id || 'Provider turn 未确认'}</div></> },
          { title: '状态', dataIndex: 'status', render: state => <Tag>{state}</Tag> }, { title: '触发', dataIndex: 'trigger_kind' },
        ]} />
        <Transcript key={provider.record_id} run={run} record={provider} />
      </> : <>
        <Descriptions className="session-facts" size="small" column={1} items={[
          { key: 'item', label: '工作项', children: label }, { key: 'providers', label: '已发现 provider', children: `${records.length} 条，其中 ${records.filter(historical).length} 条历史` },
          { key: 'generation', label: 'Assignment generation', children: [...new Set(records.map(record => record.assignment_generation ?? '未记录'))].join(', ') },
        ]} />
        <Title level={4}>Provider sessions · 包括历史</Title>
        <Table rowKey="record_id" size="small" pagination={false} scroll={{ x: 650 }} dataSource={records} columns={[
          { title: 'Native session / Physical 记录', key: 'identity', render: (_, record) => <SessionLink run={run} selected={{ ...agent, provider: record.record_id }} onSelect={onSelect}>
            <code>{record.native_session_id || '原生身份未确认'}</code><div className="subtle">{record.record_id}</div></SessionLink> },
          { title: '状态', key: 'state', render: (_, record) => <SessionState session={record} /> },
          { title: 'Provider / Profile', key: 'provider', render: (_, record) => <>{record.provider}<div className="subtle">{record.profile_id}</div></> },
          { title: 'Turns', key: 'turns', render: (_, record) => record.source_mode === 'archive' && !record.turns ? '未保存' : record.turns?.length || 0 },
        ]} />
      </>}
  </section>;
}
