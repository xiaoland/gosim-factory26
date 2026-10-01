import { ActionButton, Hint, Notice, Row, Stack, StatusBadge, UserAvatar } from '@/components/console-ui';
import { api, url } from './http';
import { useState } from 'react';
import { CircleCheck, ChevronDown, EyeOff, Eye, MessageSquare, ChevronUp, User } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { type Action, type Comment } from './api';
import { Markdown } from './Markdown';

interface Props {
  run: string;
  comments: Comment[];
  writable: boolean;
  busy: boolean;
  onReply: (id: number) => void;
  onAction: (action: Action) => void;
  onHide: (id: number) => void;
}

function time(value: string) {
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function CommentCard({ comment, expandedBody, depth, ...props }: Props & {
  comment: Comment; expandedBody?: string | null; depth: number;
}) {
  const [showHidden, setShowHidden] = useState(false);
  const id = Number(comment.database_id);
  const hidden = comment.minimized || comment.lifecycle === 'hidden';
  const needsBody = (hidden || comment.body == null) && !comment.deleted;
  const fetched = useQuery({
    queryKey: ['comment', props.run, id],
    queryFn: ({ signal }) => api<Comment[]>(url('/api/comment', { run: props.run, id }), signal),
    enabled: showHidden && needsBody,
    refetchInterval: showHidden && needsBody ? 5000 : false,
  });
  const body = hidden
    ? (showHidden ? fetched.data?.find(c => Number(c.database_id) === id)?.body : null)
    : comment.body ?? expandedBody ?? (showHidden ? fetched.data?.find(c => Number(c.database_id) === id)?.body : null);
  const resolved = comment.resolved || comment.folded;
  return <article className={`comment-card ${hidden ? 'comment-hidden' : ''}`} style={{ marginLeft: Math.min(depth, 5) * 22 }} id={`comment-${id}`}>
    <Row className="comment-head" gap={10} align="center" wrap>
      <UserAvatar size={26} className={comment.author.login === 'external' ? 'external-avatar' : ''} />
      <strong>{comment.author.login}</strong>
      {comment.author.login === 'external' && <StatusBadge tone="blue">人工</StatusBadge>}
      <a href={`#comment-${id}`} className="comment-number">#{id}</a>
      <Hint title={comment.created_at}><span className="subtle">{time(comment.created_at)}</span></Hint>
      {comment.reply_to && <a href={`#comment-${comment.reply_to}`} className="subtle">回复 #{comment.reply_to}</a>}
      {hidden && <StatusBadge icon={<EyeOff />}>已隐藏</StatusBadge>}
      {resolved && <StatusBadge tone="success" icon={<CircleCheck />}>已解决</StatusBadge>}
    </Row>
    <div className="comment-body">
      {comment.deleted ? <span className="subtle">评论已删除</span> : body != null ? <Markdown body={body} /> : <Row align="center" wrap>
        <span className="subtle">{hidden ? '隐藏的正文' : '折叠的正文'}</span>
        <ActionButton size="sm" variant="ghost" icon={<Eye />} pending={fetched.isFetching} onClick={() => setShowHidden(true)}>展开正文</ActionButton>
      </Row>}
      {fetched.error && showHidden && <Notice tone="error" title="正文读取失败" description={<pre>{fetched.error.message}</pre>} />}
      {comment.minimized_reason && <div className="hidden-reason"><EyeOff /> 隐藏原因：{comment.minimized_reason}</div>}
    </div>
    <Row className="comment-footer" justify="space-between" gap={8} wrap>
      {props.writable ? <Row gap={4} wrap>
        <ActionButton size="sm" variant="ghost" icon={<MessageSquare />} disabled={props.busy} onClick={() => props.onReply(id)}>回复</ActionButton>
        {!comment.deleted && <ActionButton size="sm" variant="ghost" disabled={props.busy}
          onClick={() => hidden ? props.onAction({ action: 'unhide', comment: id }) : props.onHide(id)}>{hidden ? '取消此条隐藏' : '隐藏此条'}</ActionButton>}
      </Row> : <span />}
      {showHidden && needsBody && <ActionButton size="sm" variant="ghost" onClick={() => setShowHidden(false)}>收起正文</ActionButton>}
    </Row>
  </article>;
}

function Thread({ nodes, ...props }: Props & { nodes: Comment[] }) {
  const [expanded, setExpanded] = useState(false);
  const root = Number(nodes[0].thread_root);
  const rootComment = nodes.find(comment => Number(comment.database_id) === root);
  const resolved = rootComment?.resolved || rootComment?.folded;
  const folded = nodes.filter(c => c.folded);
  const fetched = useQuery({
    queryKey: ['thread', props.run, root],
    queryFn: ({ signal }) => api<Comment[]>(url('/api/comment', { run: props.run, id: root, thread: 1 }), signal),
    enabled: expanded,
    refetchInterval: expanded ? 5000 : false,
  });
  const bodies = new Map(fetched.data?.map(c => [Number(c.database_id), c.body]));
  const byId = new Map(nodes.map(c => [Number(c.database_id), c]));
  const children = new Map<number | null, Comment[]>();
  for (const comment of nodes) {
    const parent = comment.reply_to && byId.has(comment.reply_to) ? comment.reply_to : null;
    const replies = children.get(parent) ?? [];
    replies.push(comment);
    children.set(parent, replies);
  }
  const ordered: Comment[] = [];
  const visited = new Set<number>();
  function visit(comment: Comment) {
    const id = Number(comment.database_id);
    if (visited.has(id)) return;
    visited.add(id);
    if (expanded || !comment.folded) ordered.push(comment);
    for (const child of children.get(id) ?? []) visit(child);
  }
  for (const comment of children.get(null) ?? []) visit(comment);
  for (const comment of nodes) visit(comment);
  // Keep the actual reply chain even when resolved ancestors are collapsed.
  function depth(comment: Comment) {
    let parent = comment.reply_to, value = 0;
    const visited = new Set([Number(comment.database_id)]);
    while (parent && byId.has(parent) && !visited.has(parent)) {
      visited.add(parent);
      value++;
      parent = byId.get(parent)!.reply_to;
    }
    return value;
  }
  return <section className="thread">
    <Row className="thread-summary" wrap>
      <Stack>
        <strong>讨论根 #{root}</strong>
        <span className="subtle">解决会折叠整串已有评论，取消解决会展开已解决历史；新回复不会自动折叠。局部整理请隐藏此条。</span>
      </Stack>
      {props.writable && rootComment && !rootComment.deleted && <ActionButton size="sm" variant="ghost" icon={<CircleCheck />} disabled={props.busy}
        onClick={() => props.onAction({ action: resolved ? 'unresolve' : 'resolve', comment: root })}>{resolved ? '取消整串解决' : '解决整串讨论'}</ActionButton>}
    </Row>
    {!!folded.length && <div className="thread-summary">
      <Row align="center" wrap><CircleCheck /><strong>已解决的历史</strong><span className="subtle">线程 #{root} · {folded.length} 条评论</span></Row>
      <ActionButton size="sm" variant="ghost" icon={expanded ? <ChevronUp /> : <ChevronDown />} pending={fetched.isFetching}
        onClick={() => setExpanded(!expanded)}>{expanded ? '收起历史' : '展开历史'}</ActionButton>
    </div>}
    {expanded && fetched.error && <Notice tone="error" title="线程读取失败" description={<pre>{fetched.error.message}</pre>} />}
    {ordered.map(comment => <CommentCard key={comment.database_id} {...props} comment={comment} depth={depth(comment)}
      expandedBody={expanded ? bodies.get(Number(comment.database_id)) : undefined} />)}
  </section>;
}

export default function Discussion(props: Props) {
  const threads = new Map<number, Comment[]>();
  for (const comment of props.comments) {
    const root = Number(comment.thread_root);
    const nodes = threads.get(root) ?? [];
    nodes.push(comment);
    threads.set(root, nodes);
  }
  return <div className="discussion">{[...threads].map(([root, nodes]) => <Thread key={root} {...props} nodes={nodes} />)}</div>;
}
