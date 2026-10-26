# Darpan Developers

Mintlify site for [developers.drpn.ai](https://developers.drpn.ai): Darpan's GraphQL API, self-hosting, and engineering internals. Product and release documentation for people using the app lives in [darpan-docs](https://github.com/drpn-ai/darpan-docs) at [docs.drpn.ai](https://docs.drpn.ai).

## Content model

- `graphql/**` is the GraphQL API: hand-written guides plus pages generated from the SDL (`queries`, `objects`, `enums`, `scalars`). The site opens on `graphql/overview`.
- `graphql-reference/` holds the SDL snapshot and the example request and response for each query.
- `self-host/**` covers running Darpan yourself: local setup, environments, production, and local troubleshooting.
- `backend/**` and `engineering/**` explain the Moqui backend engine, the frontend app, and the engineering workflow.
- `api-reference/**` documents the internal JSON-RPC API (`/rpc/json`). It is listed in `.mintignore` and never published. It stays here so the service-catalog drift check keeps it accurate.

## GraphQL reference

Edit the schema descriptions in the backend (`moqui-gql`), not the generated pages. Then:

```bash
python3 scripts/generate_graphql_reference.py            # regenerate from graphql-reference/schema.graphql
python3 scripts/generate_graphql_reference.py --check    # fail if the committed pages are out of date
python3 scripts/generate_graphql_reference.py --check --sdl-url https://<instance>/rest/s1/graphql/sdl
```

## Local preview and validation

The Mintlify CLI needs Node 20:

```bash
PATH="$(brew --prefix node@20)/bin:$PATH" mint dev
PATH="$(brew --prefix node@20)/bin:$PATH" mint broken-links
PATH="$(brew --prefix node@20)/bin:$PATH" mint validate
```

## Publishing

Mintlify deploys from `main` after a push.
