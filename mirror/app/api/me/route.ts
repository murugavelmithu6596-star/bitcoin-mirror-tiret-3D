import { requirePrivatePerson } from "../../../lib/auth";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const person = await requirePrivatePerson(request);
  if (person instanceof Response) return person;

  return Response.json(
    {
      name: person.name || "You",
      email: person.email || "",
      private: true,
      simulated: person.simulated,
      visibility: person.appVisibility,
    },
    { headers: { "cache-control": "private, no-store" } },
  );
}
