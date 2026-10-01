"""Dijkstra, greedy best-first and A* exactly as the report's pseudocode states them.

All three share one loop.  The priority queue uses lazy deletion: an improved
entry is pushed again and stale entries are skipped when they surface, which
has the same effect as Insert-or-Decrease-Key.  Ties are broken first in, first
out, by a counter stored in every entry.

  mode='dijkstra'  key = g               closed set, relaxation (Algorithm 1)
  mode='greedy'    key = h               a vertex is marked when first reached (Algorithm 3)
  mode='astar'     key = g + h           closed set, relaxation (Algorithm 4)
  mode='reopen'    key = g + h           a closed vertex that gets a smaller g
                                         goes back into the queue (Theorem 2)
"""
import heapq
import math


def haversine_km(p, q):
    """Great-circle distance in km between (longitude, latitude) points."""
    (lon1, lat1), (lon2, lat2) = p, q
    r = 6371.0
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = f2 - f1, math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def search(adj, s, t, h, mode, trace=False):
    """Run one search.  adj[u] is a list of (v, w).  h(v) is the heuristic.

    Returns a dict with the extraction order, the path, its cost and, when
    trace=True, a snapshot of the queue before every extraction.
    """
    g = {s: 0.0}
    parent = {s: None}
    tie = 0
    if mode == 'dijkstra':
        key = lambda v: g[v]
    elif mode == 'greedy':
        key = lambda v: h(v)
    else:
        key = lambda v: g[v] + h(v)
    pq = [(key(s), tie, s)]
    closed = set()
    discovered = {s}
    order, steps = [], []
    while pq:
        if trace:
            live = {}
            for k, _, v in pq:
                if v not in closed and (mode == 'greedy' or abs(k - key(v)) < 1e-9):
                    live[v] = (g[v], h(v), g[v] + h(v))
            steps.append(dict(open=live))
        k, _, u = heapq.heappop(pq)
        if u in closed:
            if trace:
                steps.pop()
            continue
        if mode != 'greedy' and abs(k - key(u)) > 1e-9:   # stale entry
            if trace:
                steps.pop()
            continue
        closed.add(u)
        order.append(u)
        if trace:
            steps[-1]['extract'] = u
            steps[-1]['updates'] = []
        if u == t:
            break
        for v, w in adj[u]:
            if mode == 'greedy':
                if v in discovered:
                    continue
                discovered.add(v)
                g[v] = g[u] + w
                parent[v] = u
                tie += 1
                heapq.heappush(pq, (key(v), tie, v))
                if trace:
                    steps[-1]['updates'].append((v, g[v]))
                continue
            if v in closed and mode != 'reopen':
                continue
            ng = g[u] + w
            if v not in g or ng < g[v] - 1e-12:
                g[v] = ng
                parent[v] = u
                closed.discard(v)            # only matters for mode='reopen'
                tie += 1
                heapq.heappush(pq, (key(v), tie, v))
                if trace:
                    steps[-1]['updates'].append((v, ng))
    path = []
    if t in parent and t in closed:
        n = t
        while n is not None:
            path.append(n)
            n = parent[n]
        path.reverse()
    cost = sum(w for a, b in zip(path, path[1:]) for v, w in adj[a] if v == b)
    return dict(order=order, path=path, cost=cost, g=g, steps=steps)


def undirected(edge_list):
    """edge_list of (a, b, w) -> adjacency lists, each edge both ways."""
    adj = {}
    for a, b, w in edge_list:
        adj.setdefault(a, []).append((b, w))
        adj.setdefault(b, []).append((a, w))
    return adj


def exact_to_goal(adj, t):
    """h*(v) for every v: Dijkstra from the goal (the graphs are undirected)."""
    return search(adj, t, None, lambda v: 0, 'dijkstra')['g']
