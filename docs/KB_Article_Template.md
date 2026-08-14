# Knowledge Base Article Template

Use this structure when writing a `KnowledgeArticle` (via `POST /api/knowledge`). Consistent structure makes articles easier to search and faster for other engineers to apply during a live incident.

Maps to the `KnowledgeArticle` model: the `title` field is your article title, and everything below the title becomes the `content` field. `tags` should be a short comma-separated list of searchable keywords (matched via `ILIKE` on `GET /api/knowledge/search`).

---

## Template

```
## Problem
One or two sentences describing the symptom, from the user's or reporter's perspective.
Avoid technical jargon here — this is what someone searching by symptom will match against.

## Affected System(s)
Which application(s) this applies to. Use the exact application name(s) as they appear
in the Applications inventory, so this article surfaces for the right incidents.

## Cause
The root cause, once known. If multiple causes can produce the same symptom, list them.

## Resolution
Step-by-step fix, numbered, in the order an engineer should actually perform them.
Be specific — include exact settings, commands, or UI paths, not vague instructions.

## Prevention / Notes
Anything that would prevent this recurring, or context worth knowing next time
(e.g., "this tends to happen after X maintenance window", "check Y first before assuming Z").

Tags: comma, separated, lowercase, keywords
```

---

## Filled Example

**Title:** Password reset emails not arriving — SPF/DKIM misconfiguration

**Content:**

```
## Problem
Users request a password reset via the Council Portal but never receive the reset email,
even after multiple attempts and checking spam folders.

## Affected System(s)
Council Portal

## Cause
The mail-sending domain's SPF record did not include the third-party transactional email
provider's sending IP range. Some receiving mail servers (particularly Outlook/Exchange)
silently drop or spam-folder mail that fails SPF alignment, rather than bouncing it —
which is why the sender-side logs showed "delivered" with no visible failure.

## Resolution
1. Confirm the issue: check the transactional email provider's dashboard for the affected
   user's email address — look for a "delivered" status with a corresponding SPF/DKIM
   "soft fail" or "fail" flag in the message headers.
2. Retrieve the current SPF TXT record for the sending domain (`dig TXT <domain>` or via
   DNS provider dashboard).
3. Add the missing `include:` mechanism for the transactional email provider to the SPF
   record (provider's documentation will list the exact value, e.g. `include:spf.provider.com`).
4. Confirm DKIM signing is enabled and the DKIM DNS record is published and verified in
   the provider's dashboard.
5. Allow up to 24–48 hours for DNS propagation, though most resolvers pick up changes
   within a few hours.
6. Ask the affected user (or a test account) to request a new password reset and confirm
   delivery.
7. Re-check message headers on the successful delivery to confirm SPF/DKIM now show "pass".

## Prevention / Notes
Any time a new transactional email provider or sending domain is added, SPF/DKIM records
must be updated as part of that change — this is easy to miss since the sender-side logs
show "delivered" regardless, giving a false sense that email is working correctly.
Consider adding a DMARC report address to catch alignment failures proactively next time.

Tags: email, password-reset, spf, dkim, council-portal, deliverability
```

---

## Search behavior

Articles are matched via case-insensitive partial match (`ILIKE '%term%'`) against `title`, `content`, and `tags` — searching "SPF" or "password reset" or "council portal" would all surface this article. Favor including likely search terms naturally in the Problem/Cause sections rather than only in tags.