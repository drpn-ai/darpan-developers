# Darpan developer documentation instructions

## About this project

- This is the Mintlify site for developers.drpn.ai: the GraphQL API, self-hosting, and engineering internals.
- User-level product docs and release notes live in `drpn-ai/darpan-docs` (docs.drpn.ai). Do not add them here; link to them with absolute `https://docs.drpn.ai/...` URLs.
- Pages are MDX files with YAML frontmatter. Navigation, branding, and redirects live in `docs.json`.
- Run `mint broken-links` and `mint validate` (Node 20) before publishing broad changes. Without the CLI, run `jq empty docs.json`.

## Content boundaries

- GraphQL is Darpan's external API. It is read-only: do not document or propose mutations.
- `/rpc/json` (JSON-RPC) is internal. `api-reference/**` stays in `.mintignore`, out of `docs.json`, and unlinked from published pages. Keep it accurate with `scripts/check_service_catalog.py`.
- The API explorer's request examples (`graphql-reference/explorer.openapi.json`) are generated from `graphql-reference/examples/*.graphql`, and its playground calls the API straight from the browser (`proxy: false`); an instance must list `https://developers.drpn.ai` in `webapp_public_api_origins`, never in `webapp_allow_origins`.
- The generated GraphQL pages come from the SDL. Change the schema description in `moqui-gql`, regenerate, and commit both. Generate from the deployed SDL (`--sdl-url`), not from a checked-in doc you have not compared.
- Backend docs must be grounded in the Darpan Moqui component at `<moqui-framework>/runtime/component/darpan`. Frontend docs must be grounded in `darpan-ui/src`.
- Everything here is public. Do not publish credentials, API keys, tenant data, customer data, private URLs, or cookies.

## Terminology

- Use "Darpan" for the product.
- Use "API key" for a `dgql_` GraphQL key. Each key belongs to one tenant.
- Use "reconciliation run" for an executed compare workflow and "audit" for a tenant's scheduled whole-system check.
- Use "RuleSet" for the rules-backed reconciliation model.

## Style

- Voice and register: follow `VOICE.md`. It is internal and must never be added to `docs.json`.
- Use active voice, second person, and sentence-case headings.
- Use code formatting for fields, types, queries, file names, commands, and paths.
- Confirm repository names against the live GitHub API (`gh api repos/<owner>/<repo> --jq '.full_name'`), not a local remote.

## Publishing

Mintlify deploys from `main` after a push. Keep `docs.json` navigation in sync with moved or renamed pages, and add a redirect when a published path changes.
