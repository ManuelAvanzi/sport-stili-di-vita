// Variante Cloudflare Worker dello stesso backend (per deploy serverless gratuito).
// Deploy:  npx wrangler deploy server/worker.js --name svs-ai
// Poi:     npx wrangler secret put API_KEY
// Config:  variabili PROVIDER / MODEL / ALLOWED_ORIGIN nel dashboard o in wrangler.toml
import { extract, advise } from "./ai.js";

export default {
  async fetch(request, env) {
    const ORIGINS = (env.ALLOWED_ORIGIN || "https://manuelavanzi.github.io").split(",").map(s => s.trim());
    const origin = request.headers.get("origin") || "";
    const dev = origin.startsWith("http://localhost:") || origin.startsWith("http://127.0.0.1:");
    const allow = ORIGINS.includes("*") ? "*" : (ORIGINS.includes(origin) || dev ? origin : ORIGINS[0]);
    const headers = {
      "access-control-allow-origin": allow,
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type",
      "content-type": "application/json; charset=utf-8",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
    if (request.method !== "POST") return json({ error: "solo POST" }, 405, headers);
    try {
      const url = new URL(request.url);
      const data = await request.json().catch(() => ({}));
      if (url.pathname === "/api/extract") return json(await extract(env, data.images), 200, headers);
      if (url.pathname === "/api/advise") return json(await advise(env, data.kind, data.data), 200, headers);
      return json({ error: "endpoint sconosciuto" }, 404, headers);
    } catch (e) {
      return json({ error: String(e.message || e).slice(0, 300) }, e.status && e.status < 500 ? e.status : 502, headers);
    }
  },
};

function json(body, status, headers) {
  return new Response(JSON.stringify(body), { status, headers });
}
