import { useState } from 'react';
import { Alert, Avatar, Button, Flex, Space, Tag, Tooltip } from 'antd';
import { CheckCircleOutlined, DownOutlined, EyeInvisibleOutlined, EyeOutlined, MessageOutlined, UpOutlined, UserOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { api, url, type Action, type Comment } from './api';
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
    <Flex className="comment-head" gap={10} align="center" wrap>
      <Avatar size={26} icon={<UserOutlined />} className={comment.author.login === 'external' ? 'external-avatar' : ''} />
      <strong>{comment.author.login}</strong>
      {comment.author.login === 'external' && <Tag color="blue">人工</Tag>}
      <a href={`#comment-${id}`} className="comment-number">#{id}</a>
      <Tooltip title={comment.created_at}><span className="subtle">{time(comment.created_at)}</span></Tooltip>
      {comment.reply_to && <a href={`#comment-${comment.reply_to}`} className="subtle">回复 #{comment.reply_to}</a>}
      {hidden && <Tag icon={<EyeInvisibleOutlined />}>已隐藏</Tag>}
      {resolved && <Tag color="success" icon={<CheckCircleOutlined />}>已解决</Tag>}
    </Flex>
    <div className="comment-body">
      {comment.deleted ? <span className="subtle">评论已删除</span> : body != null ? <Markdown body={body} /> : <Space wrap>
        <span className="subtle">{hidden ? '隐藏的正文' : '折叠的正文'}</span>
        <Button size="small" type="text" icon={<EyeOutlined />} loading={fetched.isFetching} onClick={() => setShowHidden(true)}>展开正文</Button>
      </Space>}
      {fetched.error && showHidden && <Alert type="error" showIcon title="正文读取失败" description={<pre>{fetched.error.message}</pre>} />}
      {comment.minimized_reason && <div className="hidden-reason"><EyeInvisibleOutlined /> 隐藏原因：{comment.minimized_reason}</div>}
    </div>
    <Flex className="comment-footer" justify="space-between" gap={8} wrap>
      {props.writable ? <Space size={4} wrap>
        <Button size="small" type="text" icon={<MessageOutlined />} disabled={props.busy} onClick={() => props.onReply(id)}>回复</Button>
        {!comment.deleted && <Button size="small" type="text" disabled={props.busy}
          onClick={() => hidden ? props.onAction({ action: 'unhide', comment: id }) : props.onHide(id)}>{hidden ? '取消此条隐藏' : '隐藏此条'}</Button>}
      </Space> : <span />}
      {showHidden && needsBody && <Button size="small" type="text" onClick={() => setShowHidden(false)}>收起正文</Button>}
    </Flex>
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
    <Flex className="thread-summary" wrap>
      <Space direction="vertical" size={2}>
        <strong>讨论根 #{root}</strong>
        <span className="subtle">解决会折叠整串已有评论，取消解决会展开已解决历史；新回复不会自动折叠。局部整理请隐藏此条。</span>
      </Space>
      {props.writable && rootComment && !rootComment.deleted && <Button size="small" type="text" icon={<CheckCircleOutlined />} disabled={props.busy}
        onClick={() => props.onAction({ action: resolved ? 'unresolve' : 'resolve', comment: root })}>{resolved ? '取消整串解决' : '解决整串讨论'}</Button>}
    </Flex>
    {!!folded.length && <div className="thread-summary">
      <Space wrap><CheckCircleOutlined /><strong>已解决的历史</strong><span className="subtle">线程 #{root} · {folded.length} 条评论</span></Space>
      <Button size="small" type="text" icon={expanded ? <UpOutlined /> : <DownOutlined />} loading={fetched.isFetching}
        onClick={() => setExpanded(!expanded)}>{expanded ? '收起历史' : '展开历史'}</Button>
    </div>}
    {expanded && fetched.error && <Alert type="error" showIcon title="线程读取失败" description={<pre>{fetched.error.message}</pre>} />}
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
