export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const SYSTEM = `You are Mirror, a private personal reflection companion.
Speak briefly, warmly, and specifically. Help the user notice patterns,
name feelings, and choose a small next step. Never claim to be a therapist
or give medical advice. Keep replies under 120 words unless asked for more.`;

function localReflect(messages: ChatMessage[]): string {
  const last = [...messages].reverse().find((m) => m.role === "user");
  const text = (last?.content || "").trim();
  const lower = text.toLowerCase();

  if (!text) {
    return "I'm here. What feels most present for you right now?";
  }

  if (/(anxious|worried|stress|overwhelm)/.test(lower)) {
    return `I hear the tension in what you shared. Name one thing you can set down for the next hour — a task, a worry, or a screen — and one breath you can take before you start again. What would that small release look like?`;
  }

  if (/(sad|lonely|empty|hurt|grief)/.test(lower)) {
    return `There's weight in those words. Stay with one detail that feels true, without fixing it yet. If a kinder sentence to yourself were possible tonight, what would it be?`;
  }

  if (/(angry|frustrated|mad|annoyed)/.test(lower)) {
    return `Anger often points to a boundary. What felt crossed or ignored? Mirror that back in one clear line, then decide whether you need space, a conversation, or simply acknowledgment.`;
  }

  if (/(happy|grateful|proud|excited|good)/.test(lower)) {
    return `Hold that brightness for a moment. What made it possible — a person, a choice, or a quiet habit? Naming it helps Mirror keep that path visible next time.`;
  }

  if (/(decid|choice|should i|stuck)/.test(lower)) {
    return `Two options often hide a value. If you chose the path that protects your energy this week, which way tilts? Say the trade-off out loud once — then pick the smaller reversible step.`;
  }

  const snippet = text.length > 90 ? `${text.slice(0, 87)}…` : text;
  return `You said: “${snippet}.” What part of that feels most true if you say it again slowly? Mirror can stay with that thread — or shift to what you want tomorrow to feel like.`;
}

export async function reflect(
  messages: ChatMessage[],
): Promise<{ reply: string; mode: "live" | "local" }> {
  const key = process.env.OPENAI_API_KEY?.trim() ?? "";
  if (!key) {
    return { reply: localReflect(messages), mode: "local" };
  }

  try {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        authorization: `Bearer ${key}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        temperature: 0.7,
        max_tokens: 280,
        messages: [{ role: "system", content: SYSTEM }, ...messages.slice(-12)],
      }),
    });

    if (!res.ok) {
      return { reply: localReflect(messages), mode: "local" };
    }

    const data = (await res.json()) as {
      choices?: { message?: { content?: string } }[];
    };
    const reply = data.choices?.[0]?.message?.content?.trim();
    if (!reply) return { reply: localReflect(messages), mode: "local" };
    return { reply, mode: "live" };
  } catch {
    return { reply: localReflect(messages), mode: "local" };
  }
}

export const PROMPTS = [
  "What am I avoiding that still wants my attention?",
  "Where did I feel most like myself today?",
  "What would a gentler version of this week look like?",
  "Who or what restored my energy recently?",
  "If tomorrow had one clear intention, what is it?",
];
