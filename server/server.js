// Backend AI per "Sport e Stili di Vita" — Node.js >= 18, zero dipendenze.
// Avvio:  PROVIDER=anthropic API_KEY=sk-... node server/server.js
// Env:    PROVIDER (anthropic|openai|mock)  API_KEY  MODEL  PORT (default 8787)
//         ALLOWED_ORIGIN (default: sito GitHub Pages; più origini separate da virgola, "*" per tutte)
import http from "node:http";
import { extract, advise } from "./ai.js";

const env = process.env;
const PORT = Number(env.PORT || 8787);
const ORIGINS = (env.ALLOWED_ORIGIN || "https://manuelavanzi.github.io").split(",").map(s => s.trim());

// Rate limit semplice per IP: max 20 richieste al minuto.
const hits = new Map();
function limited(ip) {
  const now = Date.now();
  const q = (hits.get(ip) || []).filter(t => now - t < 60_000);
  q.push(now); hits.set(ip, q);
  return q.length > 20;
}

function cors(req, res) {
  const origin = req.headers.origin || "";
  const dev = origin.startsWith("http://localhost:") || origin.startsWith("http://127.0.0.1:");
  const ok = ORIGINS.includes("*") ? "*" : (ORIGINS.includes(origin) || dev ? origin : ORIGINS[0]);
  res.setHeader("access-control-allow-origin", ok);
  res.setHeader("access-control-allow-methods", "POST, OPTIONS");
  res.setHeader("access-control-allow-headers", "content-type");
  res.setHeader("access-control-max-age", "86400");
}

function send(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(data);
}

const server = http.createServer(async (req, res) => {
  cors(req, res);
  if (req.method === "OPTIONS") { res.writeHead(204); return res.end(); }
  if (req.method !== "POST") return send(res, 405, { error: "solo POST" });
  const ip = req.socket.remoteAddress || "?";
  if (limited(ip)) return send(res, 429, { error: "troppe richieste, riprova tra un minuto" });

  let body = "";
  req.on("data", c => { body += c; if (body.length > 10_000_000) req.destroy(); });
  req.on("end", async () => {
    try {
      const data = body ? JSON.parse(body) : {};
      if (req.url === "/api/extract") return send(res, 200, await extract(env, data.images));
      if (req.url === "/api/advise") return send(res, 200, await advise(env, data.kind, data.data));
      send(res, 404, { error: "endpoint sconosciuto" });
    } catch (e) {
      send(res, e.status && e.status < 500 ? e.status : 502, { error: String(e.message || e).slice(0, 300) });
    }
  });
});

server.listen(PORT, () => console.log(`AI backend (${env.PROVIDER || "anthropic"}) su http://localhost:${PORT}`));
