import { lazy, Suspense, useEffect, useState } from 'react';
import { LayoutGrid, House, RotateCw } from 'lucide-react';
import { ActionButton, Choice, Hint, LoadingSkeleton, Notice, StatusBadge } from '@/components/console-ui';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Home from './Home';
import { registeredRuns } from './runs';
import { useNavigation } from './navigation';
import RunOverview from './RunOverview';

const BraidRun = lazy(() => import('./BraidRun'));

export default function App() {
  const [pendingNavigation, setPendingNavigation] = useState<(() => void) | null>(null);
  const client = useQueryClient();
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const { run, selected, missing, update, cancel } = useNavigation(dirty, busy, proceed => {
    setPendingNavigation(() => proceed);
  });
  const runs = useQuery({ queryKey: ['runs'], queryFn: ({ signal }) => registeredRuns(signal), refetchInterval: 5000, retry: false });
  const currentRun = runs.data?.find(value => value.id === run);
  useEffect(() => { window.scrollTo({ top: 0 }); }, [run]);
  useEffect(() => {
    function protect(event: BeforeUnloadEvent) { if (dirty || busy) { event.preventDefault(); event.returnValue = ''; } }
    window.addEventListener('beforeunload', protect);
    return () => window.removeEventListener('beforeunload', protect);
  }, [dirty, busy]);
  function home() { update({ run: '', selected: null }); }
  function refresh() {
    void runs.refetch();
    void client.invalidateQueries();
  }
  return <div className="console-app">
    <header className="app-header">
      <a className="brand" href="/" aria-label="Factory26 Exp Console 首页" onClick={event => { event.preventDefault(); home(); }}>
        <span className="brand-mark"><LayoutGrid size={19} /></span><strong>Factory26</strong><span>Exp Console</span></a>
      <div className="run-select"><Choice label="选择运行" value={run || ''} placeholder={runs.isPending ? '读取登记…' : '选择已登记运行'} disabled={busy || runs.isPending}
        onChange={value => update({ run: value, selected: null })}
        options={runs.data?.map(value => ({ value: value.id, label: <span className="inline-flex items-center gap-2"><span>{value.task || value.label} · {value.target || '目标未知'} · {value.id.slice(0, 8)}</span><StatusBadge>{value.mode === 'archive' ? '归档' : value.activity === 'active' ? 'active' : value.lifecycle || '状态未知'}</StatusBadge></span> })) || []} /></div>
      <div className="header-status">{!!run && <ActionButton variant="ghost" icon={<House />} disabled={busy} onClick={home}>首页</ActionButton>}
        <Hint title="刷新登记及当前页面数据"><ActionButton variant="ghost" size="icon" aria-label="刷新" icon={<RotateCw />} onClick={refresh} /></Hint></div>
    </header>
    <main className="workspace">
      {runs.error && <Notice className="error-alert" tone="error" title="运行登记读取失败" description={<pre>{runs.error.message}</pre>} />}
      {missing ? <Notice tone="error" title="页面不存在" description={<><p>此路径不是有效的 Console 页面。</p><ActionButton onClick={home}>返回首页</ActionButton></>} /> : runs.isPending ? <LoadingSkeleton /> : !runs.data ? <ActionButton onClick={refresh}>重新读取登记</ActionButton> : !run ? <Home runs={runs.data} busy={busy} onOpen={value => update({ run: value, selected: null })} />
        : !currentRun ? <Notice tone="error" title="此运行未登记" description={<><p>链接中的运行 ID：<code>{run}</code>。页面保留此身份，不切换到其它运行。</p><ActionButton onClick={home}>返回首页</ActionButton></>} />
          : <RunOverview runId={run} currentRun={currentRun} />}
    </main>
    <AlertDialog open={!!pendingNavigation} onOpenChange={open => { if (!open) { cancel(); setPendingNavigation(null); } }}><AlertDialogContent>
      <AlertDialogHeader><AlertDialogTitle>当前草稿尚未提交</AlertDialogTitle><AlertDialogDescription>切换将丢弃当前标题、正文或评论草稿。</AlertDialogDescription></AlertDialogHeader>
      <AlertDialogFooter><AlertDialogCancel>继续编辑</AlertDialogCancel><AlertDialogAction onClick={() => { setDirty(false); pendingNavigation?.(); setPendingNavigation(null); }}>丢弃并切换</AlertDialogAction></AlertDialogFooter>
    </AlertDialogContent></AlertDialog>
  </div>;
}
