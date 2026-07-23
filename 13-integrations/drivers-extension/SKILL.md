---
name: drivers-extension
description: >-
  Extends the chat repo with a new channel connector driver (inbound webhook
  normalize, optional verify, outbound send). Use when adding a messaging
  channel, a new `connectorKind`, WhatsApp/Slack/Discord/email integration,
  or when the user asks how to register drivers, `ConnectorDriver`, or
  `dispatchOutbound` / inbound pipeline wiring.
---

# Connector drivers extension

This codebase uses **one generic webhook route** and **one outbound dispatcher**. New channels are added as **drivers** plus **registry** and **installation** rows—not new API routes per provider.

## Architecture (do not break)

| Piece | Role |
|--------|------|
| `app/api/integrations/[installationId]/webhook/route.ts` | Loads installation → `runInboundPipeline` (provider-agnostic) |
| `core/inbound/pipeline.ts` | `getConnectorDriver` → optional `verifyWebhook` → `normalize` → enqueue or sync ingest |
| `core/outbound/dispatch.ts` | `getInstallationById` → `getConnectorDriver` → `outbound.send` |
| `core/connectors/types.ts` | `ConnectorDriver`, `InboundEvent`, `OutboundPayload` contracts |
| `core/connectors/registry.ts` | `Map` of `kind` → driver |
| `drivers/*.ts` | Provider-specific parse + send |

Reference implementation: `drivers/telegram.ts`.

## Checklist: new driver

1. **Implement** `drivers/<kind>.ts` exporting `const <kind>Driver` as `satisfies ConnectorDriver`.
2. **Register** in `core/connectors/registry.ts` (`drivers` map).
3. **Seed installation(s)** in `core/installations/repo.ts` (or your DB): `connectorKind` must equal `driver.kind`, `config` shape must match what the driver reads in `normalize` / `send`.
4. **Tests**: `drivers/<kind>.test.ts` for `inbound.normalize` and `outbound.send`; extend `core/connectors/registry.test.ts` for `getConnectorDriver("<kind>")`.

Do **not** add `POST /api/.../telegram`-style routes for each channel.

## `ConnectorDriver` shape

```ts
export type ConnectorDriver = {
  kind: string; // stable id, stored on installation
  inbound?: InboundCapability;  // verifyWebhook?, normalize
  outbound?: OutboundCapability; // send
};
```

- **Inbound optional**: if missing, pipeline returns 400 (“no inbound support”).
- **Outbound optional**: if missing, `dispatchOutbound` throws.

## Inbound: `normalize`

**Input:** `{ headers, rawBody, config, installation }` (see `InboundCapability` in `core/connectors/types.ts`).

**Output:** `Promise<InboundEvent[]>` — often one event, or `[]` if the payload is irrelevant (non-message update, unsupported type, parse failure you choose to ignore).

**Map into `InboundEvent`:**

- `workspaceId` — from `installation.workspaceId`
- `connector.kind` — use the same string as `driver.kind`; `connector.installationId` — `installation.id`
- `conversation.externalChatId` — string the provider uses to address the chat (thread/DM/channel)
- `actor` — `externalUserId`, `role` (`"customer"` | `"agent"` | `"system"`), optional `displayName`
- `event` — at minimum: `kind` (e.g. `"message.created"`), `externalEventId` (idempotency-friendly), `occurredAt` (ISO), `text` for text messages
- For threading / agent `replyToMessageId`: set `externalMessageId` and optional `replyToExternalMessageId` (strings; provider-specific validation happens in outbound)
- `raw` — optional, for debugging (avoid huge blobs in production)

**Do not** call ingest or queues from the driver; the pipeline does that.

## Optional: `verifyWebhook`

Use for HMAC/signature checks. Throwing stops the pipeline; the webhook route maps **`WebhookError`** to HTTP status. Importing `WebhookError` from `pipeline.ts` **from a driver** can create a **circular import** (`pipeline` → `registry` → driver → `pipeline`). Prefer:

- extracting `WebhookError` to a small module (e.g. `core/inbound/webhook-error.ts`) used by route + drivers, or
- throwing generic `Error` (caller returns 500 until you refactor).

## Outbound: `send`

**Input:** `{ config, installation, target: { externalChatId }, payload }`.

**`OutboundPayload` (discriminated union):**

- `kind: "text"` — `text`, optional `replyToExternalMessageId`
- `kind: "reaction"` — `externalMessageId`, `emoji` (empty string = remove bot reaction where the provider supports it; Telegram: `setMessageReaction` with empty `reaction` array)

Validate ids in the driver if the API requires a specific format. Return `{ ok: true }` or throw on failure.

## Agent / threading

Channel agents pass `replyToExternalMessageId` through `dispatchOutbound`; instructions stay **channel-agnostic** (`core/agents/channel-instructions.ts`, `inject-user-message-context.ts`). Do not bake provider names into agent prompts when adding a driver.

## Local testing

- Set `INGRESS_SYNC=1` so `runInboundPipeline` runs `ingestInboundEvent` inline (see `core/inbound/pipeline.ts`).
- POST raw provider JSON to `/api/integrations/<installationId>/webhook` with a matching installation id.

## Further reading

- Design rationale: [docs/ingress/generic-webhook-dispatch.md](../../../docs/ingress/generic-webhook-dispatch.md)
