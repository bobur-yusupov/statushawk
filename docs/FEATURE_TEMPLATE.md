# Feature name

|Metadata|Details|
|--------|-------|
|Status|Draft / In Review / Approved / Implemented|
|Author|@GitHubUsername|
|Created|YYYY-MM-DD"|
|Ticket/Issue|#[Issue Number]|

## 1. Summary

A 2-3 sentence "elevator pitch" of the feature. Example: Add the ability for users to receive downtime alerts via a Discord Webhook, not just Email.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: Users miss email alerts because they live in chat apps.
- Desired state: Critical alerts appear instantly in their team chat.

### 2.2 Goals

- Allow users to paste a Discord Webhook URL.
- Send a JSON payload when a monitor goes DOWN or UP.

### 2.3 Out of Scope (Non-Goals)

- We are not building a Discord Bot (two-way communication), just a one-way webhook.

## 3. Detailed Desgin

### 3.1. User Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- User navigates to Monitors > [Monitor Name] > Alerting.
- User sees a new section "Integrations".
- User selects "Discord" from a dropdown.
- Input field appears: "Webhook URL".
- User clicks "Save" (or "Test Integration").

### 3.2. Database changes

List new tables, columns, or indexes. Use your Schema Dictionary format.

- **Table**: AlertChannel (Existing)
- **Column**: type (Enum) -> Add 'DISCORD'
- **Column**: config (JSONB) -> Store {"url": "..."} here.

### 3.3. API Changes

Define the endpoints using the project's JSON standard.

**Endpoint**: `POST /api/v1/integrations/test/`

- Request

```json
{ 
    "type": "discord", 
    "url": "https://discord.com/api/webhooks/..." 
}
```

- Response

```json
{
    "status": "ok",
    "data": { "delivered": true }
}
```

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

- Runner Service: When an incident is created, the NotificationTask checks the AlertChannel type.
- Formatter: If type is DISCORD, format the message using Discord's specific JSON embed structure (color red for down, green for up).

## 4. Security Considerations

- **Validation**: How do we ensure the user doesn't paste a malicious URL (SSRF attack)?
    1. Mitigation: The backend must validate the URL host is actually
- **Permissions**: Can a "Read Only" member add a webhook? (No, must be Admin).
- **Encryption**: Is the Webhook URL sensitive? (Yes, treat it like a password).

## 5. Edge cases and testing

### 5.1 Edge cases

- **Rate Limiting**: What if Discord blocks our IP? (We should catch 429 errors and retry with exponential backoff).
- **Invalid URL**: What if the user deletes the webhook on Discord's side? (We should verify the webhook exists before saving).
- **Long Messages**: What if the error message is longer than Discord's 2000 char limit? (Truncate it).

### 5.2 Testing & strategy

- **Unit Tests**: Test the DiscordFormatter class (does it produce valid JSON?).
- **Integration Tests**: Mock the requests.post call to ensure the pipeline triggers the sender.
- **Manual Verification**: Create a real Discord channel and spam it with test alerts.

## 6. Deployment / Rollout

- **Migrations**: Requires a DB migration for the new Enum value.
- **Feature Flag**: Is this behind a flag? `ENABLE_DISCORD_INTEGRATION = True`
