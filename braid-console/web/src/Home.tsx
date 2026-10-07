import { ActionButton, EmptyState, Notice, Row, StatusBadge } from '@/components/console-ui';
import { Card } from '@/components/ui/card';
import { Archive, ArrowRight, FolderKanban, Radio } from 'lucide-react';
import { isBraidRun, type RegisteredRun } from './runs';

function stateLabel(run: RegisteredRun) {
  if (run.mode === 'archive') return '归档 · 保存状态';
  if (run.lifecycle) return `已保存 · ${run.lifecycle}`;
  if (run.activity === 'active') return '现场 · active';
  return '已登记 · 状态未知';
}

function RegistrationNote() {
  return <section className="registration-note">
    <h4>运行事实</h4>
    <p>列表来自生产者保存的 manifest/status 事实；未归档运行仍可只读查看，但不会因此被视为现场控制对象。</p>
    <span className="muted">此页面不启动实验、不补建历史材料，也不提供手动登记或运行控制。</span>
  </section>;
}

export default function Home({ runs, busy, onOpen }: {
  runs: RegisteredRun[]; busy: boolean; onOpen: (run: string) => void;
}) {
  return <section className="home" aria-label="实验首页">
    <div className="home-heading"><div><span className="home-eyebrow">FACTORY26 / EXPERIMENTS</span><h1>实验工作台</h1>
      <p className="muted">选择运行，查看状态、原生过程、资源、用量、日志和保存结果；Braid 运行另有协作视图。</p></div>
      <StatusBadge>{runs.length} 个已登记运行</StatusBadge></div>
    {!!runs.length && <div className="run-overview" aria-label="运行概览">{[
      { label: '已登记运行', value: runs.length, icon: FolderKanban },
      { label: '运行中', value: runs.filter(run => run.lifecycle === 'running').length, icon: Radio },
      { label: '保存归档', value: runs.filter(run => run.mode === 'archive').length, icon: Archive },
    ].map(metric => <div key={metric.label}><metric.icon aria-hidden="true" /><span>{metric.label}</span><strong>{metric.value}</strong></div>)}</div>}
    {!runs.length ? <section className="home-empty"><EmptyState description="尚未登记运行" />
      <p className="muted">服务已就绪；登记实际现场或已有归档后，它们会显示在这里。</p></section>
      : <div className="run-grid">{runs.map(run => <Card className="run-card" key={run.id}>
        <Row align="center" wrap><StatusBadge tone="blue">{isBraidRun(run) ? 'Braid' : run.harness}</StatusBadge><StatusBadge icon={run.mode === 'archive' ? <Archive /> : run.activity === 'active' ? <Radio /> : <FolderKanban />}>{stateLabel(run)}</StatusBadge></Row>
        <h3>{run.label}</h3><span className="run-id muted">{run.id}</span>
        <dl className="run-facts"><div><dt>Variant</dt><dd>{run.facts?.variant || run.variant || '未知 · 未保存'}</dd></div>
          <div><dt>实验名</dt><dd>{run.facts?.experiment_name || '未知 · 未保存'}</dd></div>
          <div><dt>记录中的状态</dt><dd>{run.facts?.status || run.lifecycle || '未知 · 未保存'}{run.facts?.updated_at && <small>{run.facts.updated_at}</small>}</dd></div></dl>
        <div className="run-capabilities">
          <p>只读查看生产者保存的事实；运行控制使用 Lab 命令。</p>
        </div>
        {run.access_error && <Notice tone="error" title="接入核对失败" description={<pre>{run.access_error}</pre>} />}
        {run.mode === 'archive' && <details className="run-coverage"><summary>保存材料范围与缺口</summary>{run.coverage.map((message, index) => <p key={index}>{message}</p>)}</details>}
        <details className="run-source"><summary>运行事实来源</summary><p>{run.facts?.record || '未登记生产者记录'}</p>
          {run.facts?.sha256 && <p>SHA-256: {run.facts.sha256}</p>}{run.facts?.error && <p>{run.facts.error}</p>}
          <p>这是生产者保存时的记录，不代表此刻的执行状态；协作对象终态不推导实验完成。</p></details>
        <ActionButton variant="default" icon={<ArrowRight />} disabled={busy} onClick={() => onOpen(run.id)}>查看运行</ActionButton>
      </Card>)}</div>}
    <RegistrationNote />
  </section>;
}
