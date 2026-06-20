# MCP Servers

Configured in `.mcp.json` at the repo root (shared, project-scoped). On first
use Claude Code will ask you to approve each project server.

## google-flights

- **Package:** [`google-flights-mcp`](https://github.com/tistaharahap/google-flights-mcp) (PyPI), runs via `uvx`.
- **API key:** none — uses public Google Flights data via the `fast-flights` library.
- **Note:** pinned to `fast-flights==2.2`. The library's 3.0 release changed its
  API and breaks the server (`ImportError: cannot import name 'FlightData'`), so
  the config passes `--with fast-flights==2.2`.
- **Capabilities:** one-way / round-trip flight search, airport lookup, price
  comparison, multi-passenger, all seat classes.

## google-maps

- **Package:** [`@cablate/mcp-google-map`](https://github.com/cablate/mcp-google-map), runs via `npx`.
- **API key required:** set `GOOGLE_MAPS_API_KEY` in the environment. The config
  references it as `${GOOGLE_MAPS_API_KEY}` so the secret is never committed.
- **Get a key:** Google Cloud Console → create an API key, then enable
  **Places API (New)** and **Routes API** for the project.
- **Set it:** export `GOOGLE_MAPS_API_KEY=...` in your shell/environment (or add
  it to this session's environment variables), then restart Claude Code.
- **Capabilities:** geocoding, directions, place search, distance matrix,
  elevation, and more (18 tools).

## Verify

```bash
claude mcp list
```
