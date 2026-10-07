import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, File, Folder, Link, RotateCw, TriangleAlert } from 'lucide-react';
import { ActionButton, Choice, EmptyState, LoadingSkeleton, Notice, Row } from '@/components/console-ui';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ProviderSession } from './api';
import { api, url } from './http';
import { Markdown } from './Markdown';

type Source = 'workspace' | 'origin';
type EntryKind = 'directory' | 'file' | 'symlink' | 'submodule' | 'unsupported';
interface CodeEntry { name: string; path: string; kind: EntryKind; size?: number }
interface CodeDocument {
  kind: Exclude<EntryKind, 'unsupported'>;
  path: string;
  root: string;
  observed_at: string;
  entries?: CodeEntry[];
  content?: string;
  size?: number;
  notice?: string;
  commit?: string;
}
interface OriginRefs {
  refs: { ref: string; commit: string }[];
  root: string;
  observed_at: string;
}
interface CodeSource { run: string; source: Source; provider?: string; commit?: string }
interface Position { path: string; kind: EntryKind; expanded: string[]; preview: boolean }
interface Workspace { key: string; path?: string | null; records: ProviderSession[] }
const initialPosition: Position = { path: '', kind: 'directory', expanded: [], preview: false };

function codeQuery(source: CodeSource, path: string) {
  return {
    queryKey: ['code', source.run, source.source, source.provider || null, source.commit || null, path],
    queryFn: ({ signal }: { signal: AbortSignal }) => api<CodeDocument>(url('/api/code', {
      run: source.run, source: source.source, path,
      ...(source.source === 'workspace' ? { provider: source.provider! } : { commit: source.commit! }),
    }), signal),
    retry: false,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  };
}
function parentPath(path: string) { return path.slice(0, Math.max(0, path.lastIndexOf('/'))); }
function recordLabel(record: ProviderSession) {
  const item = record.work_item_kind && record.work_item_id ? `${record.work_item_kind} #${record.work_item_id}` : '工作项未记录';
  return `${record.profile_id} · ${record.provider} · ${item} · ${record.status} · ${record.record_id}`;
}
function workspaceGroups(records: ProviderSession[]): Workspace[] {
  const groups = new Map<string, Workspace>();
  for (const record of records) {
    const key = record.worktree ? `path:${record.worktree}` : `record:${record.record_id}`;
    const group = groups.get(key);
    if (group) group.records.push(record);
    else groups.set(key, { key, path: record.worktree, records: [record] });
  }
  return [...groups.values()];
}
function EntryIcon({ kind, open }: { kind: EntryKind; open?: boolean }) {
  if (kind === 'directory') return <>{open ? <ChevronDown /> : <ChevronRight />}<Folder /></>;
  return kind === 'symlink' ? <Link /> : kind === 'submodule' || kind === 'unsupported' ? <TriangleAlert /> : <File />;
}

function CodeTree({ source, path = '', name = '根目录', position, onSelect, onToggle }: {
  source: CodeSource; path?: string; name?: string; position: Position;
  onSelect: (entry: Pick<CodeEntry, 'path' | 'kind'>) => void; onToggle: (path: string) => void;
}) {
  const open = path === '' || position.expanded.includes(path);
  const query = useQuery({ ...codeQuery(source, path), enabled: open });
  return <li>
    <button type="button" className={`file-browser-tree-row${position.path === path ? ' is-selected' : ''}`}
      aria-expanded={open} aria-current={position.path === path ? 'true' : undefined} title={path || '/'}
      onClick={() => { onSelect({ path, kind: 'directory' }); if (path) onToggle(path); }}>
      <EntryIcon kind="directory" open={open} /><span>{name}</span>
    </button>
    {open && <>
      {query.isPending && <span className="file-browser-meta" role="status">正在读取目录…</span>}
      {query.error && <Notice className="file-browser-error" tone="error" title={`目录 ${path || '/'} 读取失败`}
        description={<pre>{query.error.message}</pre>} />}
      {query.data?.notice && <Notice tone="warning" title="目录读取提示" description={<pre>{query.data.notice}</pre>} />}
      {query.data?.kind === 'directory' && (query.data.entries?.length ? <ul className="file-browser-tree-list">
        {query.data.entries.map(entry => entry.kind === 'directory'
          ? <CodeTree key={entry.path} source={source} path={entry.path} name={entry.name} position={position} onSelect={onSelect} onToggle={onToggle} />
          : <li key={entry.path}><button type="button" className={`file-browser-tree-row${position.path === entry.path ? ' is-selected' : ''}`}
            aria-current={position.path === entry.path ? 'true' : undefined} title={entry.path} onClick={() => onSelect(entry)}>
            <EntryIcon kind={entry.kind} /><span>{entry.name}</span>
            {entry.kind !== 'file' && <span className="file-browser-meta">{entry.kind === 'symlink' ? '符号链接' : entry.kind === 'submodule' ? '子模块' : '特殊文件（不可预览）'}</span>}
          </button></li>)}
      </ul> : <span className="file-browser-meta">空目录</span>)}
    </>}
  </li>;
}

function FileReader({ document, preview }: { document: CodeDocument; preview: boolean }) {
  if (document.kind === 'directory') return <EmptyState description={document.entries?.length
    ? `${document.entries.length} 个条目。展开目录并选择文件以阅读。` : '空目录'} />;
  if (document.kind === 'symlink' || document.kind === 'submodule') return <>
    <Notice title={document.kind === 'symlink' ? '符号链接：不读取目标内容' : '子模块：不读取外部仓库内容'}
      description={document.notice ? <pre>{document.notice}</pre> : undefined} />
    {document.content !== undefined && <pre className="file-browser-source"><code>{document.content}</code></pre>}
  </>;
  return <>
    {document.notice && <Notice tone="warning" title="文件读取提示" description={<pre>{document.notice}</pre>} />}
    {document.content !== undefined ? preview
      ? <div className="file-browser-preview">{document.content ? <Markdown body={document.content} /> : <EmptyState description="空文件" />}</div>
      : <pre className="file-browser-source"><code>{document.content}</code></pre>
      : !document.notice && <EmptyState description="服务未返回文本内容" />}
  </>;
}

function Browser({ run, records, originOnly }: { run: string; records: ProviderSession[]; originOnly: boolean }) {
  const [selectedSource, setSelectedSource] = useState<Source>();
  const source = originOnly ? 'origin' : selectedSource || (records.length ? 'workspace' : 'origin');
  const workspaces = workspaceGroups(records);
  const [workspaceKey, setWorkspaceKey] = useState<string>();
  const workspace = workspaces.find(group => group.key === workspaceKey) || (workspaces.length === 1 ? workspaces[0] : undefined);
  const [selectedRef, setSelectedRef] = useState<string>();
  const [versions, setVersions] = useState<Record<string, string>>({});
  const [positions, setPositions] = useState<Record<string, Position>>({});
  const [updateError, setUpdateError] = useState<string>();
  const refs = useQuery({
    queryKey: ['code-refs', run], queryFn: ({ signal }) => api<OriginRefs>(url('/api/code/refs', { run }), signal),
    enabled: !!run && source === 'origin', retry: false, staleTime: Infinity,
    refetchOnWindowFocus: false, refetchOnReconnect: false,
  });
  const commit = selectedRef ? versions[selectedRef] : undefined;
  const contextKey = source === 'workspace' ? `workspace:${workspace?.key || ''}` : `origin:${selectedRef || ''}`;
  const position = positions[contextKey] || initialPosition;
  const codeSource: CodeSource = { run, source,
    ...(source === 'workspace' ? { provider: workspace?.records[0].record_id } : { commit }) };
  const ready = !!run && (source === 'workspace' ? !!workspace : !!commit);
  const selected = useQuery({ ...codeQuery(codeSource, position.path), enabled: ready });
  const directoryPath = position.kind === 'directory' ? position.path : parentPath(position.path);
  const directory = useQuery({ ...codeQuery(codeSource, directoryPath), enabled: ready });
  const reader = useRef<HTMLDivElement>(null);
  const tree = useRef<HTMLElement>(null);
  const scroll = useRef<Record<string, number>>({});
  const readerKey = `${contextKey}:${commit || ''}:${position.path}:${position.preview}`;
  const treeKey = `${contextKey}:${commit || ''}:tree`;
  useLayoutEffect(() => {
    if (reader.current) reader.current.scrollTop = scroll.current[readerKey] || 0;
  }, [readerKey, selected.data]);
  useLayoutEffect(() => {
    if (tree.current) tree.current.scrollTop = scroll.current[treeKey] || 0;
  }, [treeKey, ready]);
  function move(next: Partial<Position>) {
    setPositions(current => ({ ...current, [contextKey]: { ...(current[contextKey] || initialPosition), ...next } }));
  }
  function chooseRef(ref: string) {
    const item = refs.data?.refs.find(item => item.ref === ref);
    setSelectedRef(ref);
    setUpdateError(undefined);
    if (item) setVersions(current => current[ref] ? current : { ...current, [ref]: item.commit });
  }
  async function updateBranch() {
    if (!selectedRef) return;
    setUpdateError(undefined);
    try {
      const result = await refs.refetch({ throwOnError: true });
      const branch = result.data?.refs.find(item => item.ref === selectedRef);
      if (!branch) { setUpdateError(`分支 ${selectedRef} 已不在当前列表中；仍固定阅读 ${commit}。`); return; }
      if (branch.commit !== commit) {
        setVersions(current => ({ ...current, [selectedRef]: branch.commit }));
        setPositions(current => ({ ...current, [`origin:${selectedRef}`]: initialPosition }));
      }
    } catch (error) { setUpdateError(error instanceof Error ? error.message : String(error)); }
  }
  const refNames = [...new Set([...(refs.data?.refs.map(item => item.ref) || []), ...Object.keys(versions)])];
  const currentBranch = refs.data?.refs.find(item => item.ref === selectedRef);
  const markdown = /\.(md|markdown)$/i.test(position.path) && selected.data?.kind === 'file' && selected.data.content !== undefined;
  const root = selected.data?.root || directory.data?.root || (source === 'origin' ? refs.data?.root : workspace?.path);
  let sourceDetails: ReactNode = null;
  if (source === 'workspace' && workspace) sourceDetails = <>
    <p>该会话登记目录的当前文件，非历史快照；文件仍可能变化。</p>
    <p>登记目录：<code>{workspace.path || '未登记'}</code></p>
    <details><summary>此目录的登记会话 · {workspace.records.length} 条</summary><ul>
      {workspace.records.map(record => <li key={record.record_id}>{recordLabel(record)}</li>)}
    </ul></details>
  </>;
  if (source === 'origin') sourceDetails = <>
    <p>本次运行共享 origin 的已发布提交树。选分支后固定 commit，更新需要明确操作。</p>
    {selectedRef && <p><code>{selectedRef} @ {commit}</code></p>}
    {currentBranch && currentBranch.commit !== commit && commit && <p className="file-browser-meta">分支列表记录的 commit 已改变；当前内容仍为固定版本。</p>}
    {refs.data && <p className="file-browser-meta">分支列表本次读取时间：{refs.data.observed_at}</p>}
  </>;
  return <section className="file-browser" aria-label="只读文件浏览">
    <div className="file-browser-toolbar">
      <Tabs value={source} onValueChange={value => setSelectedSource(value as Source)}><TabsList aria-label="文件来源">
        <TabsTrigger value="workspace" disabled={originOnly || !records.length}>会话工作区</TabsTrigger>
        <TabsTrigger value="origin">origin 分支</TabsTrigger>
      </TabsList></Tabs>
      {source === 'workspace' ? <Choice label="登记工作区" value={workspace?.key} placeholder="请选择登记目录"
        onChange={setWorkspaceKey} options={workspaces.map(group => ({ value: group.key,
          label: `${group.path || `未登记目录 · ${group.records[0].record_id}`} · ${group.records.length} 条会话` }))} />
        : <><Choice label="origin 分支" value={selectedRef} onChange={chooseRef} placeholder="请选择 origin 分支"
          options={refNames.map(ref => ({ value: ref, label: ref }))} disabled={!refNames.length} />
          <Row wrap><ActionButton icon={<RotateCw />} pending={refs.isFetching} onClick={() => { void refs.refetch(); }}>刷新分支列表</ActionButton>
            <ActionButton disabled={!selectedRef} pending={refs.isFetching} onClick={() => { void updateBranch(); }}>更新到分支最新</ActionButton></Row></>}
    </div>
    {source === 'workspace' && workspaces.length > 1 && !workspace && <Notice title="存在多个不同登记目录，请选择要阅读的目录"
      description="登记目录不代表当前归属；这里不会按 generation、状态或数组顺序推断当前工作区。" />}
    {source === 'origin' && refs.error && <Notice className="file-browser-error" tone="error" title="origin 分支列表读取失败"
      description={<pre>{refs.error.message}</pre>} />}
    {updateError && <Notice className="file-browser-error" tone="error" title="分支更新失败" description={<pre>{updateError}</pre>} />}
    {sourceDetails && <div className="file-browser-root">{sourceDetails}</div>}
    {!ready ? source === 'origin' && refs.isPending ? <LoadingSkeleton rows={3} /> : <EmptyState description={source === 'workspace'
      ? workspaces.length ? '请选择登记目录。' : '没有登记的工作区。'
      : refs.data && !refNames.length ? 'origin 没有已发布分支。' : '请选择 origin 分支，随后固定该分支的 commit。'} /> : <div className="file-browser-layout">
      <nav className="file-browser-tree" aria-label="文件目录" ref={tree} onScroll={event => { scroll.current[treeKey] = event.currentTarget.scrollTop; }}>
        <ul className="file-browser-tree-list"><CodeTree source={codeSource} position={position}
          onSelect={entry => move({ path: entry.path, kind: entry.kind })}
          onToggle={path => move({ expanded: position.expanded.includes(path) ? position.expanded.filter(item => item !== path) : [...position.expanded, path] })} /></ul>
      </nav>
      <section className="file-browser-reader" aria-label="文件内容">
        <header className="file-browser-reader-header">
          <strong className="file-browser-path">{position.path || '/'}</strong>
          <div className="file-browser-meta">来源：{source === 'workspace' ? '会话登记工作区' : 'origin 固定提交'} · 根目录：<code>{root || '未读取'}</code></div>
          {source === 'origin' && <div className="file-browser-meta"><code>{selectedRef} @ {commit}</code></div>}
          {selected.data && <div className="file-browser-meta">本次读取时间：{selected.data.observed_at}{selected.data.size !== undefined && ` · ${selected.data.size} 字节`}</div>}
          <Row wrap><ActionButton icon={<RotateCw />} pending={directory.isFetching} onClick={() => { void directory.refetch(); }}>刷新目录</ActionButton>
            <ActionButton icon={<RotateCw />} disabled={position.kind === 'directory'} pending={selected.isFetching && position.kind !== 'directory'}
              onClick={() => { void selected.refetch(); }}>刷新文件</ActionButton>
            {markdown && <Tabs value={position.preview ? 'preview' : 'source'} onValueChange={value => move({ preview: value === 'preview' })}>
              <TabsList aria-label="Markdown 阅读方式"><TabsTrigger value="source">源码</TabsTrigger><TabsTrigger value="preview">预览</TabsTrigger></TabsList>
            </Tabs>}
          </Row>
        </header>
        <div className="file-browser-reader-body" ref={reader} onScroll={event => { scroll.current[readerKey] = event.currentTarget.scrollTop; }}>
          {selected.error && <Notice className="file-browser-error" tone="error"
            title={selected.data ? '本次读取失败；以下内容为此前读取的缓存' : '内容读取失败'} description={<pre>{selected.error.message}</pre>} />}
          {selected.isPending ? <LoadingSkeleton rows={5} /> : selected.data && <FileReader document={selected.data} preview={markdown && position.preview} />}
        </div>
      </section>
    </div>}
  </section>;
}

export default function FileBrowser({ run, records = [], originOnly = false }: { run: string; records?: ProviderSession[]; originOnly?: boolean }) {
  return <Browser key={run} run={run} records={records} originOnly={originOnly} />;
}
