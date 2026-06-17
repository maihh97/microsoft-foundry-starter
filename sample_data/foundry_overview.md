# Contoso Health — Microsoft Foundry Adoption Brief

## Approved capabilities

- **Code Interpreter** for sandboxed data analysis and chart generation.
- **File Search** for retrieval-augmented answers over approved documents.
- **MCP (Model Context Protocol)** for connecting curated external tool servers.
- **A2A (Agent2Agent)** for delegating across specialist agents.
- **Microsoft Agent Framework** for code-first orchestration, optionally deployed as a
  **Hosted Agent** container.

## Governance rules

1. Every agent must run under a named service identity; shared credentials are not allowed.
2. Production agents require a red-team safety scan before release.
3. Patient-identifying data may only be processed by agents inside the `contosorg` resource
   group, and must never be sent to non-Microsoft tool endpoints.
4. All agent runs must emit OpenTelemetry traces to the team's Application Insights resource.