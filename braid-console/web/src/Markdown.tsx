import { Input, Tabs } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function Markdown({ body }: { body: string }) {
  return <div className="markdown"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml
    components={{ img: () => null, a: ({ children, ...props }) => <a {...props} target="_blank" rel="noreferrer">{children}</a> }}>
    {body || '（无正文）'}
  </ReactMarkdown></div>;
}

export function BodyInput({ value, onChange, label, disabled = false }: {
  value: string; onChange: (value: string) => void; label: string; disabled?: boolean;
}) {
  return <Tabs className="body-editor" size="small" items={[
    { key: 'write', label: '编辑', children: <Input.TextArea aria-label={label} value={value}
      onChange={event => onChange(event.target.value)} autoSize={{ minRows: 7, maxRows: 24 }} disabled={disabled}
      placeholder="支持 Markdown；可用 @成员名 提及负责人" /> },
    { key: 'preview', label: '预览', children: <div className="editor-preview"><Markdown body={value} /></div> },
  ]} />;
}
