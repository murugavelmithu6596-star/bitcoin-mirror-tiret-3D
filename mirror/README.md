# Mirror

Private personal AI reflection companion. Installable on a phone as a Progressive Web App.

## Privacy

- Publish **Private** so only your Cursor account can open the app (no public listing, no sign-up).
- Every `/api/*` route requires a verified Cursor identity and rejects API-key callers.
- Chat history stays in your browser `localStorage` on the device.

## Run locally

```bash
cd mirror
npm install
npm run dev
```

Open http://127.0.0.1:3000 — local identity is simulated until publish.

## Install on phone

1. Publish Mirror and choose **Private** in the Cursor publish dialog.
2. Open the private app URL while signed into Cursor on your phone.
3. **iPhone (Safari):** Share → Add to Home Screen.
4. **Android (Chrome):** Menu → Install app / Add to Home screen.

## Optional live AI

Bind `OPENAI_API_KEY` in Cursor app secrets. Without it, Mirror uses a built-in local reflection engine.
