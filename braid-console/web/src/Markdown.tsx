import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  return <Tabs className="body-editor" defaultValue="write"><TabsList aria-label={label + '模式'}><TabsTrigger value="write">编辑</TabsTrigger><TabsTrigger value="preview">预览</TabsTrigger></TabsList>
    <TabsContent value="write"><Textarea aria-label={label} value={value} rows={7} className="max-h-[600px] min-h-44 resize-y" disabled={disabled}
      onChange={event => onChange(event.target.value)} placeholder="支持 Markdown；可用 @成员名 提及负责人" /></TabsContent>
    <TabsContent value="preview"><div className="editor-preview"><Markdown body={value} /></div></TabsContent>
  </Tabs>;
}
