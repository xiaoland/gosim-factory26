import { Alert, Button, Empty, Space, Tag, Typography } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';
import type { RegisteredRun } from './runs';

const { Title, Text, Paragraph } = Typography;

function RegistrationNote() {
  return <section className="registration-note">
    <Title level={4}>登记运行</Title>
    <Paragraph>在服务所在宿主准备实际运行的 registry，然后停止此 HTTP 实例，使用配套管理 CLI 登记并重新启动。归档只读，现场须明确原路径空间、binary 和权限。</Paragraph>
    <pre>{'python3 <当前冻结程序>/service.py register --service <稳定服务目录> --registry <新增运行列表.json>'}</pre>
    <Text type="secondary">接入格式与各资源的启停归属见项目 braid-console/README.md；此页面不启动实验或补建历史材料。</Text>
  </section>;
}

export default function Home({ runs, busy, onOpen }: {
  runs: RegisteredRun[]; busy: boolean; onOpen: (run: string) => void;
}) {
  return <section className="home" aria-label="实验首页">
    <div className="home-heading"><div><Text className="home-eyebrow">FACTORY26</Text><Title level={1}>实验入口</Title>
      <Paragraph type="secondary">已登记运行的接入与保存材料。选择 Braid 运行，查看工作项、讨论和会话。</Paragraph></div>
      <Tag>{runs.length} 个已登记运行</Tag></div>
    {!runs.length ? <section className="home-empty"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="尚未登记运行" />
      <Paragraph type="secondary">服务已就绪；登记实际现场或已有归档后，它们会显示在这里。</Paragraph></section>
      : <div className="run-grid">{runs.map(run => <article className="run-card" key={run.id}>
        <Space wrap><Tag color="blue">{run.harness === 'braid' ? 'Braid' : run.harness}</Tag><Tag>{run.mode === 'archive' ? '归档 · 保存状态' : '现场 · live'}</Tag></Space>
        <Title level={3}>{run.label}</Title><Text className="run-id" type="secondary">{run.id}</Text>
        <dl className="run-facts"><div><dt>Variant</dt><dd>{run.facts.variant || '未知 · 未保存'}</dd></div>
          <div><dt>实验名</dt><dd>{run.facts.experiment_name || '未知 · 未保存'}</dd></div>
          <div><dt>记录中的状态</dt><dd>{run.facts.status || '未知 · 未保存'}{run.facts.updated_at && <small>{run.facts.updated_at}</small>}</dd></div></dl>
        <div className="run-capabilities">
          <p><strong>读取</strong>{run.read_check === 'saved-archive' ? '保存对象已核对；范围与缺口见下方' : run.read_check === 'unavailable' ? '接入不可用' : '已登记；现场状态尚未读取'}</p>
          <p><strong>人工写入</strong>{run.writable ? '已允许；执行前仍核对现场' : '不允许'}</p>
          <p><strong>暂停 / 恢复</strong>{run.controllable ? '已登记；进入详情读取实际状态' : '未登记'}</p>
        </div>
        {run.access_error && <Alert type="error" showIcon title="接入核对失败" description={<pre>{run.access_error}</pre>} />}
        {run.mode === 'archive' && <details className="run-coverage"><summary>保存材料范围与缺口</summary>{run.coverage.map((message, index) => <p key={index}>{message}</p>)}</details>}
        <details className="run-source"><summary>运行事实来源</summary><p>{run.facts.record || '未登记生产者记录'}</p>
          {run.facts.sha256 && <p>SHA-256: {run.facts.sha256}</p>}{run.facts.error && <p>{run.facts.error}</p>}
          <p>这是生产者保存时的记录，不代表此刻的执行状态；协作对象终态不推导实验完成。</p></details>
        <Button type="primary" icon={<ArrowRightOutlined />} disabled={busy || run.harness !== 'braid'} onClick={() => onOpen(run.id)}>查看 Braid 详情</Button>
      </article>)}</div>}
    <RegistrationNote />
  </section>;
}
