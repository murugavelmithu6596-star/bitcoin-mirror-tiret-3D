// Cursor app identity: simulated private-app viewer for local development.
// Private Mirror has no team roles — only the signed-in owner.

/** @type {import("./identity.js").DevViewer | null} */
export const DEV_VIEWER = {
  sub: "user:dev",
  email: "dev@example.com",
  name: "Dev Viewer",
};
