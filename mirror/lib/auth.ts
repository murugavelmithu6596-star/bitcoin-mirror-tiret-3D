import { requireIdentity } from "../cursor/identity.js";

export type PrivatePerson = {
  sub: string;
  email: string;
  name: string;
  kind: "person";
  appVisibility: "private" | "team" | "public";
  simulated: boolean;
};

/**
 * Enforce single-user private access:
 * - Platform gate (publish as private) blocks anyone who is not the owner.
 * - This helper requires a verified Cursor identity and refuses API keys.
 */
export async function requirePrivatePerson(
  request: Request,
): Promise<PrivatePerson | Response> {
  const identity = await requireIdentity(request);
  if (identity instanceof Response) return identity;

  if (identity.kind !== "person") {
    return Response.json(
      { error: "forbidden", reason: "person_only" },
      {
        status: 403,
        headers: { "cache-control": "private, no-store" },
      },
    );
  }

  return {
    sub: identity.sub,
    email: identity.email,
    name: identity.name,
    kind: "person",
    appVisibility: identity.appVisibility,
    simulated: identity.simulated === true,
  };
}
