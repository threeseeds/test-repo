#!/usr/bin/env python3
"""Second-order graph analysis and Mermaid rendering.

Edge A -> B means "B depends on A". Two views are analysed:
  explicit_only   edges with basis=explicit (the firm structure)
  with_inferred   every edge that is not rejected (inferred edges can merge loops)

Reports roots, leaves, cycles (strongly connected components), longest chains,
records that depend on something outside the graph, and records whose outputs nothing
consumes. Cycles are reported, never treated as errors.

Usage:
  graph.py RUN_DIR [--actions actions.json] [--deps dependencies.json]
           [--analysis-out analysis.json] [--mermaid dependency-graph.mmd]
           [--group none|chapter|actor] [--view explicit|all] [--hide-types enforcement]
           [--max-nodes 60]
"""
import argparse, collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_text, write_text, read_json, write_json


CONSUMING = {"triggers", "produces-input", "condition-precedent", "temporal"}
GRAPH_EXCLUDED = ("duplicate_of", "superseded_by")




def graph_nodes(actions, edges):
    recs = [r for r in actions if not any(k in r for k in GRAPH_EXCLUDED)]
    ids = [r["id"] for r in recs]
    ext = sorted({e[k] for e in edges for k in ("from", "to") if e[k].startswith("external:")})
    return recs, ids, ext


def sccs(nodes, adj):
    """Iterative Tarjan. Returns list of components (each a sorted list), in reverse topological order."""
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(sorted(adj[root])))]
        index[root] = low[root] = counter[0]; counter[0] += 1; stack.append(root); on.add(root)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]; counter[0] += 1; stack.append(w); on.add(w)
                    work.append((w, iter(sorted(adj[w]))))
                    advanced = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop(); on.discard(w); comp.append(w)
                    if w == v:
                        break
                out.append(sorted(comp))
    return out


def analyze(actions, edges):
    recs, ids, ext = graph_nodes(actions, edges)
    idset = set(ids)
    adj = {n: set() for n in ids + ext}
    radj = {n: set() for n in ids + ext}
    for e in edges:
        adj[e["from"]].add(e["to"]); radj[e["to"]].add(e["from"])
    roots = [n for n in ids if not radj[n]]
    leaves = [n for n in ids if not adj[n]]
    comps = sccs(ids + ext, adj)
    cycles = sorted([c for c in comps if len(c) > 1 or (c[0] in adj[c[0]])], key=lambda c: (len(c), c))
    # longest chain over the condensation DAG (weighted by component size)
    cid = {n: i for i, c in enumerate(comps) for n in c}
    cadj = collections.defaultdict(set)
    for u in adj:
        for v in adj[u]:
            if cid[u] != cid[v]:
                cadj[cid[u]].add(cid[v])
    best, nxt = {}, {}
    for i in range(len(comps)):          # comps are in reverse topological order: successors first
        b, n = 0, None
        for j in cadj[i]:
            if best[j] > b:
                b, n = best[j], j
        best[i] = b + len(comps[i]); nxt[i] = n
    start = max(range(len(comps)), key=lambda i: best[i]) if comps else None
    chain = []
    while start is not None:
        c = comps[start]
        chain.append(c[0] if len(c) == 1 else c)
        start = nxt[start]
    by = {r["id"]: r for r in recs}
    outgoing_consumers = collections.defaultdict(int)
    for e in edges:
        if e["type"] in CONSUMING:
            outgoing_consumers[e["from"]] += 1
    dangling = [r["id"] for r in recs if r["outputs"] and not outgoing_consumers[r["id"]]]
    ext_dep = [r["id"] for r in recs if any(x.startswith("external:") for x in radj[r["id"]])]
    open_ref = [r["id"] for r in recs if r["signal"]["type"] == "upstream_action" and r["signal"].get("ref") not in idset]
    return {"nodes": len(ids), "edges": len(edges), "roots": roots, "leaves": leaves, "cycles": cycles,
            "longest_chain": {"length": best[max(best, key=best.get)] if best else 0, "path": chain},
            "depends_on_external": ext_dep, "unresolved_upstream": open_ref,
            "dangling_outputs": dangling, "external_stubs": ext}


def analyze_views(actions, deps):
    live = [e for e in deps["edges"] if e["status"] != "rejected"]
    return {"explicit_only": analyze(actions, [e for e in live if e["basis"] == "explicit"]),
            "with_inferred": analyze(actions, live)}


def mm_id(s):
    return re.sub(r"[^A-Za-z0-9]", "_", s)


def esc(s):
    return s.replace('"', "'").replace("<", "(").replace(">", ")")


def render_mermaid(actions, deps, group="none", view="all", hide=(), nodes_only=None):
    by = {r["id"]: r for r in actions}
    edges = [e for e in deps["edges"] if e["status"] != "rejected" and e["type"] not in hide
             and (view == "all" or e["basis"] == "explicit")]
    if nodes_only is not None:
        edges = [e for e in edges if e["from"] in nodes_only and e["to"] in nodes_only]
    live_ids = {r["id"] for r in actions if not any(k in r for k in GRAPH_EXCLUDED)}
    used = sorted({e[k] for e in edges for k in ("from", "to")} | (set(nodes_only) if nodes_only is not None else live_ids))
    lines = ["flowchart LR"]

    def node(n):
        if n.startswith("external:"):
            return f'  {mm_id(n)}(["{esc(n[9:])}"])'
        r = by[n]
        who = r["actor"]["id"][4:] if r["actor"] else "?"
        return f'  {mm_id(n)}["{esc(n[2:])}<br/>{esc(r["action"]["verb"])}<br/><i>{esc(who)}</i>"]'

    grouped = collections.defaultdict(list)
    for n in used:
        if n.startswith("external:") or group == "none":
            grouped[None].append(n)
        elif group == "chapter":
            m = re.match(r"A-(\d+\.\d+)", n)
            grouped[m.group(1) if m else "?"].append(n)
        else:
            grouped[(by[n]["actor"] or {"id": "ACT-unknown"})["id"][4:]].append(n)
    for g, ns in sorted(grouped.items(), key=lambda kv: str(kv[0])):
        if g is None:
            lines += [node(n) for n in ns]
        else:
            lines.append(f'  subgraph {mm_id("g_" + g)}["{esc(g)}"]')
            lines += ["  " + node(n) for n in ns]
            lines.append("  end")
    for e in edges:
        label = esc(e["type"]) + ("" if e["basis"] == "explicit" else " (inferred)")
        arrow = "-->" if e["basis"] == "explicit" else "-.->"
        lines.append(f'  {mm_id(e["from"])} {arrow}|"{label}"| {mm_id(e["to"])}')
    return "\n".join(lines) + "\n", len(used)


def weak_components(actions, deps, hide, view):
    edges = [e for e in deps["edges"] if e["status"] != "rejected" and e["type"] not in hide
             and (view == "all" or e["basis"] == "explicit")]
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for e in edges:
        parent[find(e["from"])] = find(e["to"])
    for r in actions:
        if not any(k in r for k in GRAPH_EXCLUDED):
            find(r["id"])
    comps = collections.defaultdict(set)
    for n in list(parent):
        comps[find(n)].add(n)
    multi = [c for c in comps.values() if len(c) > 1]
    single = set().union(*[c for c in comps.values() if len(c) == 1]) if any(len(c) == 1 for c in comps.values()) else set()
    out = sorted(multi, key=lambda c: (-len(c), sorted(c)[0]))
    return out + ([single] if single else [])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--actions", default="actions.json")
    ap.add_argument("--deps", default="dependencies.json")
    ap.add_argument("--analysis-out")
    ap.add_argument("--mermaid")
    ap.add_argument("--group", choices=["none", "chapter", "actor"], default="none")
    ap.add_argument("--view", choices=["explicit", "all"], default="all")
    ap.add_argument("--hide-types", default="", help="comma-separated edge types to omit from the diagram")
    ap.add_argument("--max-nodes", type=int, default=60)
    a = ap.parse_args(argv)
    P = lambda n: n if os.path.isabs(n) else os.path.join(a.run_dir, n)
    actions, deps = read_json(P(a.actions)), read_json(P(a.deps))
    views = analyze_views(actions, deps)
    if a.analysis_out:
        write_json(P(a.analysis_out), views)
    hide = tuple(x for x in a.hide_types.split(",") if x)
    if a.mermaid:
        out = P(a.mermaid)
        full, n_nodes = render_mermaid(actions, deps, a.group, a.view, hide)
        if n_nodes <= a.max_nodes:
            write_text(out, full)
            print(f"wrote {out} ({n_nodes} nodes)")
        else:
            base, ext = os.path.splitext(out)
            comps = weak_components(actions, deps, hide, a.view)
            for i, c in enumerate(comps, 1):
                write_text(f"{base}.part{i}{ext}", render_mermaid(actions, deps, a.group, a.view, hide, nodes_only=c)[0])
            print(f"{n_nodes} nodes exceed --max-nodes {a.max_nodes}: wrote {len(comps)} component files {base}.part*{ext}")
    for name, v in views.items():
        print(f"{name}: {v['nodes']} nodes, {v['edges']} edges, {len(v['roots'])} roots, {len(v['leaves'])} leaves, "
              f"{len(v['cycles'])} cycle(s), longest chain {v['longest_chain']['length']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
