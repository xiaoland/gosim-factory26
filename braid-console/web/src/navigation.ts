import { useEffect, useRef } from 'react';
import { useBlocker, useMatches, useNavigate } from 'react-router-dom';
import type { Selection } from './api';

interface Route { run: string; selected: Selection | null }
// Explicit page identities; queries never select a run, work item or session.
// App owns the persistent workspace and editor; matched endpoints provide identity
// without remounting those drafts. Every leaf has an explicit empty view.
const PageIdentity = () => null;
export const pageRoutes = [
  { index: true, Component: PageIdentity },
  { path: 'runs/:run', Component: PageIdentity, caseSensitive: true },
  ...['issues', 'prs'].flatMap(kind => [
    { path: `runs/:run/${kind}/:id`, Component: PageIdentity, caseSensitive: true, handle: { kind: kind === 'issues' ? 'issue' : 'pr' } },
    { path: `runs/:run/${kind}/:id/agents/:agent`, Component: PageIdentity, caseSensitive: true, handle: { kind: kind === 'issues' ? 'issue' : 'pr' } },
    { path: `runs/:run/${kind}/:id/agents/:agent/providers/:provider`, Component: PageIdentity, caseSensitive: true, handle: { kind: kind === 'issues' ? 'issue' : 'pr' } },
  ]),
  { path: '*', Component: PageIdentity, handle: { missing: true } },
];
export function routeURL(run: string, selected: Selection | null) {
  if (!run) return '/';
  let path = `/runs/${encodeURIComponent(run)}`;
  if (selected) {
    path += `/${selected.kind === 'issue' ? 'issues' : 'prs'}/${selected.id}`;
    if (selected.agent) path += `/agents/${encodeURIComponent(selected.agent)}`;
    if (selected.provider && selected.agent) path += `/providers/${encodeURIComponent(selected.provider)}`;
  }
  return path;
}

export function useNavigation(dirty: boolean, busy: boolean, confirm: (proceed: () => void) => void) {
  const navigate = useNavigate();
  const match = useMatches().at(-1)!;
  const { run = '', id, agent, provider } = match.params;
  const handle = match.handle as { kind?: Selection['kind']; missing?: boolean } | undefined;
  const invalidSegment = Object.values(match.params).some(value => value && (/[\\/\x00-\x1f]/.test(value) || value === '.' || value === '..'));
  const missing = !!handle?.missing || invalidSegment || (!!id && (!/^[1-9][0-9]*$/.test(id) || !Number.isSafeInteger(Number(id))));
  const selected: Selection | null = !missing && handle?.kind && id ? { kind: handle.kind, id: Number(id), ...(agent ? { agent, provider } : {}) } : null;
  const blocker = useBlocker(dirty || busy);
  const proceeding = useRef(false);
  const conditions = useRef({ busy, confirm });
  conditions.current = { busy, confirm };
  useEffect(() => {
    if (blocker.state === 'unblocked') proceeding.current = false;
    if (blocker.state !== 'blocked') return;
    if (conditions.current.busy) blocker.reset();
    else conditions.current.confirm(() => { proceeding.current = true; blocker.proceed(); });
  }, [blocker]);
  function update(next: Route, replace = false) {
    if (!busy) void navigate(routeURL(next.run, next.selected), { replace });
  }
  return { run, selected, missing, update, cancel: () => { if (blocker.state === 'blocked' && !proceeding.current) blocker.reset(); } };
}
