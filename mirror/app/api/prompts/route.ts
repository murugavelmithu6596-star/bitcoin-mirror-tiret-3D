import { requirePrivatePerson } from "../../../lib/auth";
import { PROMPTS } from "../../../lib/reflect";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const person = await requirePrivatePerson(request);
  if (person instanceof Response) return person;

  const day = Math.floor(Date.now() / 86400000);
  const prompt = PROMPTS[day % PROMPTS.length];

  return Response.json(
    { prompt, prompts: PROMPTS },
    { headers: { "cache-control": "private, no-store" } },
  );
}