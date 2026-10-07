import { ActionButton, LoadingSkeleton, Notice, StatusBadge } from '@/components/console-ui';
import type { Item, Selection } from './api';
import { Markdown } from './Markdown';
import { SessionLink, SessionLinks, useSessions, useReview } from './Sessions';

export function ReviewLinks({ run, item, onSelect }: { run: string; item: Item; onSelect: (value: Selection) => void }) {
  if (!item.review_requests?.length) return null;
  return <div className="metadata-section"><div className="metadata-label">审阅请求 · {item.review_requests.length}</div>
    {item.review_requests.map(review => <div className="session-link" key={review.id}>
      <SessionLink run={run} selected={{ kind: 'pr', id: review.pr, review: review.id }} onSelect={onSelect}>
        审阅 #{review.id} · {review.member || '未指派'}
      </SessionLink><StatusBadge>{review.status} · {review.verdict || '尚无结论'}</StatusBadge>
    </div>)}
  </div>;
}

export default function Review({ run, selected, onSelect }: { run: string; selected: Selection; onSelect: (value: Selection) => void }) {
  const query = useReview(run, selected);
  const sessions = useSessions(run);
  const view = query.data;
  const request = view?.request;
  const conclusion = request?.conclusion;
  const relatedAgents = new Set([conclusion?.agent, view?.checkout?.agent].filter(Boolean));
  const related = (sessions.data || []).filter(record => record.group_id && relatedAgents.has(record.group_id) && record.work_item_kind === 'issue');
  const relatedIDs = [...new Set(related.map(record => record.group_id!))];
  return <section className="detail-panel">
    <ActionButton onClick={() => onSelect({ kind: 'pr', id: selected.id })}>返回 PR #{selected.id}</ActionButton>
    <div className="detail-heading"><div className="detail-eyebrow">PR #{selected.id} · REVIEW</div><h2>审阅 #{selected.review}</h2></div>
    {query.error && <Notice tone="error" title="审阅详情读取失败" description={<pre>{query.error.message}</pre>} />}
    {query.isPending ? <LoadingSkeleton rows={6} /> : view && request && <div className="detail-content">
      <StatusBadge>{request.status} · {conclusion?.verdict || '尚无结论'}</StatusBadge>
      <dl className="session-facts">
        <div><dt>执行责任</dt><dd>{view.current_member || '未记录'} · {request.responsibility} · revision {request.responsibility_revision}</dd></div>
        <div><dt>冻结候选</dt><dd><code>{request.head_commit}</code></dd></div>
        <div><dt>冻结 base</dt><dd><code>{request.base_commit}</code></dd></div>
        <div><dt>验收 Issue</dt><dd><SessionLink run={run} selected={{ kind: 'issue', id: request.issue }} onSelect={onSelect}>Issue #{request.issue}</SessionLink></dd></div>
        {view.checkout && <div><dt>候选 checkout</dt><dd>{view.checkout.member}<br /><code>{view.checkout.path}</code><br /><code>{view.checkout.commit}</code></dd></div>}
        {conclusion && <div><dt>实际结论作者</dt><dd>{conclusion.member} · {conclusion.at}<br /><code>{conclusion.agent || 'agent 未保存'}</code><br /><code>{conclusion.turn || 'turn 未保存'}</code></dd></div>}
      </dl>
      {view.freshness_errors.length > 0 && <Notice title="冻结审阅与当前候选 / 需求的差异" description={<><p>历史结论仍保留；当前适用性不能替代当时的验收结果。</p><pre>{view.freshness_errors.join('\n')}</pre></>} />}
      {request.cancelled_reason && <Notice title="取消原因" description={request.cancelled_reason} />}
      <SessionLinks run={run} selected={selected} onSelect={onSelect} />
      {!!relatedIDs.length && <div className="metadata-section"><div className="metadata-label">关联 Issue agent（由结论 / checkout 身份确认）</div>
        {relatedIDs.map(agent => { const record = related.find(record => record.group_id === agent)!; return <p key={agent}>
          <SessionLink run={run} selected={{ kind: 'issue', id: Number(record.work_item_id), agent }} onSelect={onSelect}>{agent}</SessionLink>
        </p>; })}<p className="subtle">此入口保留 Issue 会话归属；其中全部对话不等于本次审阅过程。</p></div>}
      <h3>审阅结论</h3>{conclusion ? <><Markdown body={conclusion.body} /><h4>证据入口</h4>{conclusion.evidence.map(entry => <p key={entry}><code>{entry}</code></p>)}</> : <p className="muted">尚未保存结论。</p>}
      <details className="technical-details"><summary>冻结验收需求</summary><Markdown body={request.requirements_body} /></details>
    </div>}
  </section>;
}
