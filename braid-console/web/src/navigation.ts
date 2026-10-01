import { useEffect, useRef, useState } from 'react';
import type { Selection } from './api';

interface Route { run: string; selected: Selection | null }
function readRoute(): Route {
  const params = new URLSearchParams(location.search);
  const kind = params.get('kind');
  const id = Number(params.get('id'));
  const agent = params.get('agent') || undefined;
  return { run: params.get('run') || '', selected: (kind === 'issue' || kind === 'pr') && Number.isInteger(id) && id > 0
    ? { kind, id, ...(agent ? { agent, provider: params.get('provider') || undefined } : {}) } : null };
}
export function routeURL(run: string, selected: Selection | null) {
  if (!run) return location.pathname;
  const params = new URLSearchParams({ run, ...(selected ? { kind: selected.kind, id: String(selected.id),
    ...(selected.agent ? { agent: selected.agent } : {}), ...(selected.provider ? { provider: selected.provider } : {}) } : {}) });
  return `${location.pathname}?${params}`;
}

export function useNavigation(dirty: boolean, busy: boolean, confirm: (proceed: () => void) => void) {
  const [route, setRoute] = useState(readRoute);
  const index = useRef(Number(history.state?.braidConsoleIndex) || 0);
  const restoring = useRef<{ delta: number; blocked: boolean } | null>(null);
  const accepted = useRef(false);
  const conditions = useRef({ dirty, busy, confirm });
  conditions.current = { dirty, busy, confirm };
  useEffect(() => {
    history.replaceState({ ...history.state, braidConsoleIndex: index.current }, '');
    function pop(event: PopStateEvent) {
      if (restoring.current) {
        const { delta, blocked } = restoring.current;
        restoring.current = null;
        if (!blocked) conditions.current.confirm(() => { accepted.current = true; history.go(delta); });
        return;
      }
      const nextIndex = Number(event.state?.braidConsoleIndex) || 0;
      const delta = nextIndex - index.current;
      if (!accepted.current && delta && (conditions.current.dirty || conditions.current.busy)) {
        restoring.current = { delta, blocked: conditions.current.busy };
        history.go(-delta);
        return;
      }
      accepted.current = false;
      index.current = nextIndex;
      setRoute(readRoute());
    }
    window.addEventListener('popstate', pop);
    return () => window.removeEventListener('popstate', pop);
  }, []);
  function update(next: Route, replace = false) {
    function apply() {
      if (!replace) index.current += 1;
      history[replace ? 'replaceState' : 'pushState']({ braidConsoleIndex: index.current }, '', routeURL(next.run, next.selected));
      setRoute(next);
    }
    if (replace) apply();
    else if (!busy) dirty ? confirm(apply) : apply();
  }
  return { ...route, update };
}
