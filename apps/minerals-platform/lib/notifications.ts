import nodemailer from "nodemailer";

export type AlertChannel = "email" | "webhook" | "slack" | "teams";
export type AlertMessage = { subject: string; body: string; severity: string; alertId: string; link?: string };

async function postJson(url: string, payload: unknown) {
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error(`Notification endpoint returned HTTP ${response.status}`);
}

export async function deliverAlert(channel: AlertChannel, message: AlertMessage, options: { emailTo?: string } = {}) {
  if (channel === "email") {
    const smtp = process.env.SMTP_URL;
    if (!smtp || !options.emailTo) throw new Error("SMTP_URL and email recipient are required");
    const transport = nodemailer.createTransport(smtp);
    const from = process.env.ALERT_EMAIL_FROM ?? "alerts@clearglassinc.com";
    await transport.sendMail({ from, to: options.emailTo, subject: message.subject, text: `${message.body}\n\nSeverity: ${message.severity}\nAlert: ${message.alertId}${message.link ? `\n${message.link}` : ""}` });
    return;
  }
  if (channel === "slack") {
    const url = process.env.SLACK_WEBHOOK_URL;
    if (!url) throw new Error("SLACK_WEBHOOK_URL is not configured");
    await postJson(url, { text: `*${message.subject}*\n${message.body}\nSeverity: ${message.severity}${message.link ? `\n${message.link}` : ""}` });
    return;
  }
  if (channel === "teams") {
    const url = process.env.TEAMS_WEBHOOK_URL;
    if (!url) throw new Error("TEAMS_WEBHOOK_URL is not configured");
    await postJson(url, { type: "message", attachments: [{ contentType: "application/vnd.microsoft.card.adaptive", content: { type: "AdaptiveCard", version: "1.4", body: [{ type: "TextBlock", weight: "Bolder", text: message.subject }, { type: "TextBlock", wrap: true, text: message.body }, { type: "TextBlock", text: `Severity: ${message.severity}` }] } }] });
    return;
  }
  const url = process.env.ALERT_WEBHOOK_URL;
  if (!url) throw new Error("ALERT_WEBHOOK_URL is not configured");
  await postJson(url, message);
}
