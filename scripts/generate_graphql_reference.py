#!/usr/bin/env python3
"""Generate the GraphQL reference (DAR-DOCS-003) from the SDL Darpan serves.

    python3 scripts/generate_graphql_reference.py            # regenerate from graphql-reference/schema.graphql
    python3 scripts/generate_graphql_reference.py --check    # fail if the committed pages are out of date
    python3 scripts/generate_graphql_reference.py --check --sdl-url https://<instance>/rest/s1/graphql/sdl
                                                             # fail if the DEPLOYED schema differs from the snapshot

The SDL is the single source: every description on these pages is the schema's own, so the reference cannot say
something the API does not. The snapshot comes from the backend's printSdl task (moqui-gql), which prints exactly what
/rest/s1/graphql/sdl serves. Pages under graphql/queries, graphql/objects, graphql/enums and graphql/scalars are
generated: edit the schema descriptions, not the pages. Example request and response blocks come from
graphql-reference/examples/<query>.graphql and <query>.json. Standard library only.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDL_PATH = os.path.join(ROOT, "graphql-reference", "schema.graphql")
EXAMPLES = os.path.join(ROOT, "graphql-reference", "examples")
EXPLORER = os.path.join(ROOT, "graphql-reference", "explorer.openapi.json")
OUT = "graphql"
GENERATED_DIRS = ["queries", "objects", "enums", "scalars"]
BUILTIN_SCALARS = {
    "String": "UTF-8 text.",
    "Int": "A signed 32-bit integer.",
    "Boolean": "true or false.",
    "ID": "A unique identifier, serialized as a string.",
}
TAB = "GraphQL API"
# Hand-written groups, above the generated reference: start, then tasks, then how the API behaves.
GUIDE_GROUPS = [
    {"group": "Get started", "pages": ["graphql/overview", "graphql/quickstart", "graphql/authentication",
                                       "graphql/explorer"]},
    {"group": "Common tasks", "pages": ["graphql/tasks", "graphql/tasks/check-the-morning-audit",
                                        "graphql/tasks/list-open-findings", "graphql/tasks/read-one-finding",
                                        "graphql/tasks/sync-findings", "graphql/tasks/recent-reconciliation-runs"]},
    {"group": "Using the API", "pages": ["graphql/cost-and-throttling", "graphql/pagination", "graphql/search-syntax",
                                         "graphql/errors", "graphql/versioning", "graphql/changelog"]},
]
# Queries in the order a reader needs them; a query not named here follows, alphabetically.
QUERY_ORDER = ["auditReport", "auditFinding", "findings", "reconciliationResults", "reconciliationResult"]
# The recipe pages that use each query, linked from its page.
RECIPES = {
    "auditReport": [("Check this morning's audit", "/graphql/tasks/check-the-morning-audit")],
    "auditFinding": [("Read one finding", "/graphql/tasks/read-one-finding")],
    "findings": [("List open findings", "/graphql/tasks/list-open-findings"),
                 ("Sync findings every day", "/graphql/tasks/sync-findings")],
    "reconciliationResults": [("Read recent reconciliation runs", "/graphql/tasks/recent-reconciliation-runs")],
    "reconciliationResult": [("Read recent reconciliation runs", "/graphql/tasks/recent-reconciliation-runs")],
}


# ---------------------------------------------------------------------------------------------------------------
# A small SDL parser for the subset graphql-java's SchemaPrinter writes: descriptions, type, enum, scalar.
# ---------------------------------------------------------------------------------------------------------------
TOKEN = re.compile(r'"""(?:.|\n)*?"""|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z0-9_]*|[{}():!,\[\]=@]|\S')


def tokens(sdl):
    for m in TOKEN.finditer(sdl):
        yield m.group(0)


def string_value(tok):
    if tok.startswith('"""'):
        return re.sub(r"\s+", " ", tok[3:-3]).strip()
    return json.loads(tok)


class Parser:
    def __init__(self, sdl):
        self.t = list(tokens(sdl))
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expect(self, tok):
        got = self.next()
        if got != tok:
            raise ValueError(f"expected {tok!r}, got {got!r} at token {self.i}")

    def description(self):
        if self.peek() and self.peek().startswith('"'):
            return string_value(self.next())
        return None

    def type_ref(self):
        if self.peek() == "[":
            self.next()
            inner = self.type_ref()
            self.expect("]")
            ref = "[" + inner + "]"
        else:
            ref = self.next()
        if self.peek() == "!":
            self.next()
            ref += "!"
        return ref

    def parse(self):
        types = {}
        while self.peek() is not None:
            desc = self.description()
            kw = self.next()
            if kw == "schema":
                self.skip_block()
                continue
            if kw == "directive":   # graphql-java's built-in directives (@skip, @include, ...): not documented here
                self.skip_directive()
                continue
            name = self.next()
            if kw == "scalar":
                types[name] = {"kind": "scalar", "name": name, "description": desc}
            elif kw == "enum":
                self.expect("{")
                values = []
                while self.peek() != "}":
                    vdesc = self.description()
                    values.append({"name": self.next(), "description": vdesc})
                self.expect("}")
                types[name] = {"kind": "enum", "name": name, "description": desc, "values": values}
            elif kw == "type":
                self.expect("{")
                fields = []
                while self.peek() != "}":
                    fdesc = self.description()
                    fname = self.next()
                    args = []
                    if self.peek() == "(":
                        self.next()
                        while self.peek() != ")":
                            adesc = self.description()
                            aname = self.next()
                            self.expect(":")
                            args.append({"name": aname, "type": self.type_ref(), "description": adesc})
                            if self.peek() == ",":
                                self.next()
                        self.expect(")")
                    self.expect(":")
                    fields.append({"name": fname, "type": self.type_ref(), "args": args, "description": fdesc})
                self.expect("}")
                types[name] = {"kind": "object", "name": name, "description": desc, "fields": fields}
            else:
                raise ValueError(f"unsupported SDL keyword {kw!r}")
        return types

    def skip_directive(self):
        self.expect("@")
        self.next()
        if self.peek() == "(":
            depth = 0
            while True:
                tok = self.next()
                depth += {"(": 1, ")": -1}.get(tok, 0)
                if depth == 0:
                    break
        if self.peek() == "repeatable":
            self.next()
        self.expect("on")
        self.next()
        while self.peek() == "|":
            self.next()
            self.next()

    def skip_block(self):
        self.expect("{")
        depth = 1
        while depth:
            tok = self.next()
            depth += {"{": 1, "}": -1}.get(tok, 0)


# ---------------------------------------------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------------------------------------------
def base(ref):
    return ref.replace("[", "").replace("]", "").replace("!", "")


def slug(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()   # DateTime -> date-time, ID -> id


def page_of(types, name):
    t = types.get(name)
    if t is None:
        return None
    return {"object": "objects", "enum": "enums", "scalar": "scalars"}[t["kind"]] + "/" + slug(name)


def type_link(types, ref):
    name = base(ref)
    target = page_of(types, name)
    shown = ref.replace("<", "&lt;")
    return f"[`{shown}`](/{OUT}/{target})" if target else f"`{shown}`"


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ")


def frontmatter(title, description):
    return "---\ntitle: " + json.dumps(title) + "\ndescription: " + json.dumps(description or title) + "\n---\n\n" \
        + "{/* Generated by scripts/generate_graphql_reference.py from graphql-reference/schema.graphql. Edit the " \
          "schema descriptions, not this page. */}\n\n"


def example_blocks(name):
    out = []
    q = os.path.join(EXAMPLES, name + ".graphql")
    r = os.path.join(EXAMPLES, name + ".json")
    if os.path.exists(q):
        out.append("## Example\n\n<CodeGroup>\n\n```graphql Request\n" + open(q).read().strip() + "\n```\n\n")
        if os.path.exists(r):
            out.append("```json Response\n" + open(r).read().strip() + "\n```\n\n")
        out.append("</CodeGroup>\n")
    return "".join(out)


def query_page(types, f):
    md = frontmatter(f["name"], f["description"])
    md += "```graphql\n" + signature(f) + "\n```\n\n"
    if f["args"]:
        md += "## Arguments\n\n| Argument | Type | Description |\n|---|---|---|\n"
        for a in f["args"]:
            md += f"| `{a['name']}` | {type_link(types, a['type'])} | {cell(a['description'])} |\n"
        md += "\n"
    md += "## Returns\n\n" + type_link(types, f["type"]) + "\n\n"
    md += example_blocks(f["name"])
    md += "## Try it\n\nSend " + ("this example" if os.path.exists(os.path.join(EXAMPLES, f["name"] + ".graphql"))
                                   else "a query") + " with your own key in the [API explorer](/graphql/explorer)"
    recipes = RECIPES.get(f["name"], [])
    if recipes:
        md += ", or follow " + " and ".join(f"[{title}]({href})" for title, href in recipes)
    md += ".\n"
    return md


def signature(f):
    if not f["args"]:
        return f"{f['name']}: {f['type']}"
    args = ", ".join(f"{a['name']}: {a['type']}" for a in f["args"])
    return f"{f['name']}({args}): {f['type']}"


def object_page(types, t, returned_by):
    md = frontmatter(t["name"], t["description"])
    md += "## Fields\n\n| Field | Type | Description |\n|---|---|---|\n"
    for f in t["fields"]:
        name = f"`{f['name']}`"
        if f["args"]:
            name += "<br/>" + ", ".join(f"`{a['name']}`" for a in f["args"])
        md += f"| {name} | {type_link(types, f['type'])} | {cell(f['description'])} |\n"
    refs = returned_by.get(t["name"], [])
    if refs:
        md += "\n## Returned by\n\n" + "\n".join(f"- {r}" for r in refs) + "\n"
    return md


def enum_page(t):
    md = frontmatter(t["name"], t["description"])
    md += "## Values\n\n| Value | Description |\n|---|---|\n"
    for v in t["values"]:
        md += f"| `{v['name']}` | {cell(v['description'])} |\n"
    return md


def scalar_page(t):
    return frontmatter(t["name"], t["description"])


def reachable(types, start):
    seen, todo = set(), [start]
    while todo:
        name = todo.pop()
        if name in seen or name not in types:
            continue
        seen.add(name)
        for f in types[name].get("fields", []):
            todo.append(base(f["type"]))
            for a in f["args"]:
                todo.append(base(a["type"]))
    return seen


def generate(sdl, out_root):
    types = Parser(sdl).parse()
    query = types.pop("Query")
    for name, desc in BUILTIN_SCALARS.items():   # first, so every String! / Int / ID in a table links
        types.setdefault(name, {"kind": "scalar", "name": name, "description": desc})
    returned_by = {}
    for f in query["fields"]:
        returned_by.setdefault(base(f["type"]), []).append(f"[`{f['name']}`](/{OUT}/queries/{slug(f['name'])}) query")
    for t in types.values():
        for f in t.get("fields", []):
            returned_by.setdefault(base(f["type"]), []).append(f"[`{t['name']}.{f['name']}`](/{OUT}/{page_of(types, t['name'])})")

    files = {}
    for f in query["fields"]:
        files[f"queries/{slug(f['name'])}.mdx"] = query_page(types, f)
    for t in types.values():
        path = page_of(types, t["name"]) + ".mdx"
        files[path] = {"object": lambda: object_page(types, t, returned_by), "enum": lambda: enum_page(t),
                       "scalar": lambda: scalar_page(t)}[t["kind"]]()

    # Navigation: the queries, then every object in a collapsed folder named for the query that returns it.
    # reconciliationResult and reconciliationResults share one folder; an object two folders reach is "Shared".
    fields = sorted(query["fields"], key=lambda f: (QUERY_ORDER.index(f["name"]) if f["name"] in QUERY_ORDER
                                                     else len(QUERY_ORDER), f["name"]))
    folders, roots = {}, {}
    for f in fields:
        folder = "reconciliationResults" if f["name"].startswith("reconciliationResult") else f["name"]
        roots.setdefault(folder, base(f["type"]))
        for n in reachable(types, base(f["type"])):
            if types[n]["kind"] == "object":
                folders.setdefault(n, set()).add(folder)
    objects = {}
    for n, owners in folders.items():
        objects.setdefault(next(iter(owners)) if len(owners) == 1 else None, []).append(n)
    leftovers = [n for n, t in types.items() if t["kind"] == "object" and n not in folders]
    nested = []
    for folder, root in roots.items():
        names = sorted(objects.get(folder, []), key=lambda n: (n != root, n))
        nested.append({"group": f"Returned by {folder}", "expanded": False,
                       "pages": [f"{OUT}/{page_of(types, n)}" for n in names]})
    shared = sorted(objects.get(None, []) + leftovers)
    if shared:
        nested.append({"group": "Shared", "expanded": False, "pages": [f"{OUT}/{page_of(types, n)}" for n in shared]})
    nested.append({"group": "Enums and scalars", "expanded": False,
                   "pages": sorted(f"{OUT}/{page_of(types, n)}" for n, t in types.items() if t["kind"] in ("enum", "scalar"))})
    groups = [{"group": "Queries", "pages": [f"{OUT}/queries/{slug(f['name'])}" for f in fields]},
              {"group": "Objects", "pages": nested}]

    for rel, text in files.items():
        path = os.path.join(out_root, OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
    return files, groups


def update_navigation(groups, docs_json):
    with open(docs_json) as fh:
        docs = json.load(fh)
    tabs = docs["navigation"]["tabs"]
    tab = {"tab": TAB, "icon": "brackets-curly", "groups": GUIDE_GROUPS + groups}
    existing = [i for i, t in enumerate(tabs) if t.get("tab") == TAB]
    if existing:
        tabs[existing[0]] = tab
    else:
        tabs.insert(0, tab)
    text = json.dumps(docs, indent=2, ensure_ascii=False) + "\n"
    with open(docs_json, "w") as fh:
        fh.write(text)
    return text


def update_explorer(fields, spec_json):
    """The API explorer's request examples: its own key check first, then each query's example file."""
    with open(spec_json) as fh:
        spec = json.load(fh)
    content = spec["paths"]["/rest/s1/graphql/public"]["post"]["requestBody"]["content"]["application/json"]
    examples = {"Check your key": content["examples"]["Check your key"]}
    for f in sorted(fields, key=lambda f: (QUERY_ORDER.index(f["name"]) if f["name"] in QUERY_ORDER
                                           else len(QUERY_ORDER), f["name"])):
        q = os.path.join(EXAMPLES, f["name"] + ".graphql")
        if os.path.exists(q):
            examples[f["name"]] = {"summary": f"{f['name']}: {f['description']}", "value": {"query": open(q).read().strip()}}
    content["examples"] = examples
    text = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    with open(spec_json, "w") as fh:
        fh.write(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail when the committed pages or snapshot are out of date")
    ap.add_argument("--sdl-url", help="compare against this deployed /rest/s1/graphql/sdl instead of the snapshot")
    args = ap.parse_args()

    sdl = open(SDL_PATH).read()
    if args.sdl_url:
        with urllib.request.urlopen(args.sdl_url, timeout=30) as resp:
            deployed = json.load(resp)["sdl"]
        if deployed.strip() != sdl.strip():
            print(f"DRIFT: {args.sdl_url} serves a different schema than graphql-reference/schema.graphql; "
                  "refresh the snapshot (printSdl) and regenerate.", file=sys.stderr)
            return 1
        print("deployed SDL matches the snapshot")

    if not args.check:
        for d in GENERATED_DIRS:
            target = os.path.join(ROOT, OUT, d)
            if os.path.isdir(target):
                for name in os.listdir(target):
                    os.remove(os.path.join(target, name))
        files, groups = generate(sdl, ROOT)
        update_navigation(groups, os.path.join(ROOT, "docs.json"))
        update_explorer(Parser(sdl).parse()["Query"]["fields"], EXPLORER)
        print(f"wrote {len(files)} pages under {OUT}/ and the {TAB!r} tab in docs.json")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        files, groups = generate(sdl, tmp)
        stale = []
        for rel, text in files.items():
            path = os.path.join(ROOT, OUT, rel)
            if not os.path.exists(path) or open(path).read() != text:
                stale.append(rel)
        for d in GENERATED_DIRS:
            target = os.path.join(ROOT, OUT, d)
            for name in (os.listdir(target) if os.path.isdir(target) else []):
                if f"{d}/{name}" not in files:
                    stale.append(f"{d}/{name} (no longer in the schema)")
        docs_json = os.path.join(ROOT, "docs.json")
        tmp_json = os.path.join(tmp, "docs.json")
        with open(docs_json) as src, open(tmp_json, "w") as dst:
            dst.write(src.read())
        if update_navigation(groups, tmp_json) != open(docs_json).read():
            stale.append("docs.json navigation")
        tmp_spec = os.path.join(tmp, "explorer.openapi.json")
        with open(EXPLORER) as src, open(tmp_spec, "w") as dst:
            dst.write(src.read())
        if update_explorer(Parser(sdl).parse()["Query"]["fields"], tmp_spec) != open(EXPLORER).read():
            stale.append("graphql-reference/explorer.openapi.json examples")
    if stale:
        print("STALE: regenerate with scripts/generate_graphql_reference.py:\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    print(f"{len(files)} generated pages and the navigation are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
