"""Public copy of the darpan contract for developers.drpn.ai: operator-only admin.* methods removed.

usage: public_openapi.py <generated openapi.json> <out> <previous public copy (for its description)>
"""
import json, re, sys

src, dst, public_prev = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src, encoding="utf-8"))
version = d["info"]["version"]
methods = d["x-darpan-methods"]
admin = {m for m in methods if m.startswith("admin.")}


def refs(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                out.add(v.rsplit("/", 1)[-1])
            else:
                refs(v, out)
    elif isinstance(node, list):
        for v in node:
            refs(v, out)
    return out


admin_bases = {methods[m] for m in admin}
for m in admin:
    del methods[m]


def prune(node):
    """Drop admin methods from mappings, enums, consts, and $ref items that point at dropped schemas."""
    if isinstance(node, dict):
        if isinstance(node.get("mapping"), dict):
            node["mapping"] = {k: v for k, v in node["mapping"].items() if k not in admin}
        if isinstance(node.get("enum"), list):
            node["enum"] = [v for v in node["enum"] if v not in admin]
        for v in node.values():
            prune(v)
    elif isinstance(node, list):
        node[:] = [v for v in node
                   if not (isinstance(v, dict) and ("$ref" in v and v["$ref"].rsplit("/", 1)[-1] in dropped
                                                    or v.get("const") in admin))]
        for v in node:
            prune(v)


schemas = d["components"]["schemas"]


def closure(roots):
    out, todo = set(), set(roots)
    while todo:
        n = todo.pop()
        if n in out or n not in schemas:
            continue
        out.add(n)
        todo |= refs(schemas[n], set())
    return out


def roots_of(bases):
    return {b + s for b in bases for s in ("Request", "Response", "Params", "Result") if b + s in schemas}


# A schema goes when only admin methods reach it: everything outside the admin closure stays, plus whatever the
# public methods' own schemas reach (shared types an admin method also uses).
admin_only = closure(roots_of(admin_bases))
keep = closure((set(schemas) - admin_only) | roots_of(methods.values()))
dropped = set(schemas) - keep
prune(d["paths"])
d["components"]["schemas"] = {k: v for k, v in schemas.items() if k in keep}
prune(d["components"]["schemas"])

prev = json.load(open(public_prev, encoding="utf-8"))
d["info"]["description"] = re.sub(r"darpan v[0-9.]+ contract", f"darpan v{version} contract",
                                  prev["info"]["description"], count=1)
with open(dst, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
