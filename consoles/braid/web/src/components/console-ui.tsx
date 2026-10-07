import { useState, type ComponentProps, type CSSProperties, type ReactNode } from 'react';
import { AlertCircle, Check, Copy, Info, Inbox, LoaderCircle, TriangleAlert, User, X } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Skeleton } from './ui/skeleton';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';

export function ActionButton({ icon, pending, children, disabled, variant = 'outline', ...props }: ComponentProps<typeof Button> & { icon?: ReactNode; pending?: boolean }) {
  return <Button {...props} variant={variant} disabled={disabled || pending} aria-busy={pending || undefined}>
    {pending ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : icon}{children}
  </Button>;
}

export function Row({ gap = 8, align, justify, wrap, className, style, ...props }: ComponentProps<'div'> & {
  gap?: number; align?: CSSProperties['alignItems']; justify?: CSSProperties['justifyContent']; wrap?: boolean;
}) {
  return <div {...props} className={cn('flex min-w-0', className)} style={{ gap, alignItems: align, justifyContent: justify, flexWrap: wrap ? 'wrap' : undefined, ...style }} />;
}
export function Stack({ className, ...props }: ComponentProps<'div'>) {
  return <div {...props} className={cn('flex min-w-0 flex-col gap-1', className)} />;
}
export function StatusBadge({ tone = 'default', icon, className, children }: {
  tone?: string; icon?: ReactNode; className?: string; children: ReactNode;
}) {
  return <Badge variant="outline" className={cn('status-badge', `tone-${tone}`, className)}>{icon}{children}</Badge>;
}
export function UserAvatar({ size = 26, className }: { size?: number; className?: string }) {
  return <Avatar style={{ width: size, height: size }} className={className}><AvatarFallback><User size={size * .55} aria-hidden="true" /></AvatarFallback></Avatar>;
}
export function Notice({ tone = 'info', title, description, className, onClose }: {
  tone?: 'error' | 'warning' | 'info'; title: ReactNode; description?: ReactNode; className?: string; onClose?: () => void;
}) {
  const Icon = tone === 'error' ? AlertCircle : tone === 'warning' ? TriangleAlert : Info;
  return <Alert variant={tone === 'error' ? 'destructive' : 'default'} className={cn('notice', `notice-${tone}`, onClose && 'pr-12', className)}>
    <Icon aria-hidden="true" /><AlertTitle>{title}</AlertTitle>{description && <AlertDescription>{description}</AlertDescription>}
    {onClose && <Button size="icon-sm" variant="ghost" className="absolute right-2 top-2" aria-label="关闭提示" onClick={onClose}><X /></Button>}
  </Alert>;
}
export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return <div className="space-y-3 py-3" role="status" aria-label="正在读取"><Skeleton className="mb-5 h-5 w-1/3" />
    {Array.from({ length: rows }, (_, index) => <Skeleton key={index} className={cn('h-3', index === rows - 1 ? 'w-2/3' : 'w-full')} />)}</div>;
}
export function EmptyState({ description }: { description: ReactNode }) {
  return <div className="empty-state"><div className="empty-icon"><Inbox aria-hidden="true" /></div><p>{description}</p></div>;
}
export function Hint({ title, children }: { title: ReactNode; children: ReactNode }) {
  return <Tooltip><TooltipTrigger asChild>{children}</TooltipTrigger><TooltipContent>{title}</TooltipContent></Tooltip>;
}
export function Choice({ value, onChange, options, placeholder, label, disabled, className }: {
  value?: string; onChange: (value: string) => void; options: { value: string; label: ReactNode }[]; placeholder?: string;
  label: string; disabled?: boolean; className?: string;
}) {
  return <Select value={value} onValueChange={onChange} disabled={disabled}><SelectTrigger className={cn('w-full min-w-0', className)} aria-label={label}>
    <SelectValue placeholder={placeholder} /></SelectTrigger><SelectContent>{options.map(option => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent></Select>;
}
export function EditorDialog({ title, description, open, onClose, busy, children, footer, wide }: {
  title: ReactNode; description: string; open: boolean; onClose: () => void; busy?: boolean; children: ReactNode; footer: ReactNode; wide?: boolean;
}) {
  return <Dialog open={open} onOpenChange={value => { if (!value && !busy) onClose(); }}><DialogContent className={cn('max-h-[85vh] overflow-y-auto', wide && 'sm:max-w-3xl')} showCloseButton={!busy}>
    <DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription></DialogHeader>
    {children}<DialogFooter>{footer}</DialogFooter>
  </DialogContent></Dialog>;
}
export function CopyText({ children, className }: { children: string | null | undefined; className?: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(children || ''); setCopied(true); }
    catch (error) { toast.error('复制失败', { description: error instanceof Error ? error.message : String(error) }); }
  }
  return <span className={cn('inline-flex max-w-full items-start gap-2', className)}><span className="min-w-0 break-all">{children}</span>
    <Button size="icon-sm" variant="ghost" aria-label={copied ? '再次复制身份' : '复制身份'} onClick={() => { void copy(); }}>{copied ? <Check /> : <Copy />}</Button></span>;
}
