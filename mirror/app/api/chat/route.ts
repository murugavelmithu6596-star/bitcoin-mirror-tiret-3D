import { requirePrivatePerson } from "../../../lib/auth";
import { reflect, type ChatMessage } from "../../../lib/reflect";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const person = await requirePrivatePerson(request);
  if (person instanceof Response) return person;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { error: "invalid_json" },
      { status: 400, headers: { "cache-control": "private, no-store" } },
    );
  }

  const messages = (body as { messages?: unknown }).messages;
  if (!Array.isArray(messages) || messages.length === 0) {
    return Response.json(
      { error: "messages_required" },
      { status: 400, headers: { "cache-control": "private, no-store" } },
    );
  }

  const cleaned: ChatMessage[] = [];
  for (const item of messages.slice(-12)) {
    if (!item || typeof item !== "object") continue;
    const role = (item as { role?: unknown }).role;
    const content = (item as { content?: unknown }).content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") {
      continue;
    }
    const text = content.trim().slice(0, 4000);
    if (!text) continue;
    cleaned.push({ role, content: text });
  }

  if (cleaned.length === 0 || cleaned.at(-1)?.role !== "user") {
    return Response.json(
      { error: "user_message_required" },
      { status: 400, headers: { "cache-control": "private, no-store" } },
    );
  }

  const { reply, mode } = await reflect(cleaned);
  return Response.json(
    { reply, mode, owner: person.name || "You" },
    { headers: { "cache-control": "private, no-store" } },
  );
}
