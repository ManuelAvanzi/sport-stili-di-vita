# Backend AI (proxy con chiave)

Rende attive la lettura del referto e la generazione dei consigli anche sul sito
pubblico, per qualunque visitatore. La chiave API resta **solo qui** (mai nel
browser) e il provider è intercambiabile.

## Cambiare AI = cambiare due variabili

| Variabile | Con Claude (Anthropic) | Con ChatGPT (OpenAI) | Collaudo senza chiave |
|---|---|---|---|
| `PROVIDER` | `anthropic` | `openai` | `mock` |
| `API_KEY`  | `sk-ant-...` (console.anthropic.com) | `sk-...` (platform.openai.com) | non serve |
| `MODEL` (opz.) | default `claude-opus-5` | default `gpt-4o` | — |

Nient'altro cambia: stessa app, stessi endpoint (`POST /api/extract`,
`POST /api/advise`). I prompt stanno in `ai.js` sul server (il client manda solo
i dati), così il proxy non è utilizzabile come chatbot generico.

## Avvio locale (Node ≥ 18, zero dipendenze)

```bash
PROVIDER=mock node server/server.js
```

poi nel sito impostare `window.SVS_API = "http://localhost:8787"` (riga già
predisposta in `index.html`). Con `PROVIDER=mock` risponde con dati di prova
senza consumare nulla.

## Deploy consigliato: Cloudflare Workers (gratis)

```bash
npx wrangler deploy server/worker.js --name svs-ai
npx wrangler secret put API_KEY        # incolla la chiave quando richiesto
```

Nel dashboard del worker impostare le variabili `PROVIDER` (ed eventualmente
`MODEL`, `ALLOWED_ORIGIN`). L'URL risultante (es.
`https://svs-ai.<account>.workers.dev`) va messo in `index.html`:

```html
<script>window.SVS_API = "https://svs-ai.<account>.workers.dev"</script>
```

In alternativa `server.js` gira su qualsiasi macchina Node (anche il server
della piattaforma): stessa logica, stesse variabili.

## Sicurezza e privacy

- CORS ristretto al dominio del sito (`ALLOWED_ORIGIN`, default GitHub Pages).
- Rate limit 20 richieste/minuto per IP (nel worker è per-istanza: per un uso
  intenso passare a Cloudflare KV o a un rate limit a monte).
- Nessun dato viene salvato: puro passaggio verso il provider. Il prompt di
  estrazione vieta di trascrivere nomi e cognomi presenti nel referto.

## Costi indicativi

Una lettura di referto (2 immagini) costa pochi centesimi; una generazione di
consigli meno di un centesimo con i modelli di fascia media. Per contenere i
costi si può impostare `MODEL` su un modello più economico (es.
`claude-sonnet-5`); la qualità dell'estrazione numerica va ricollaudata con i
PDF di `test-data/`.
