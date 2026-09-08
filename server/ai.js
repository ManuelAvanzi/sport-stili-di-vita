// Nucleo AI provider-agnostico per "Sport e Stili di Vita".
// Il provider si sceglie con le variabili d'ambiente:
//   PROVIDER = "anthropic" | "openai" | "mock"
//   API_KEY  = chiave del provider scelto
//   MODEL    = opzionale (default: claude-opus-5 / gpt-4o)
// I prompt vivono QUI (non arrivano dal client): il proxy non è un LLM generico.
// Nota: gli stessi prompt esistono anche nell'app per la modalità claude.ai —
// se si modificano, aggiornarli in entrambi i posti.

export const EXTRACT_PROMPT = `Le immagini mostrano un referto di analisi della composizione corporea InBody (bioimpedenziometria), in italiano, eventualmente diviso in metà superiore e inferiore che si sovrappongono.
IMPORTANTE per la privacy: se nel referto compaiono nome, cognome o altri dati identificativi di una persona, NON trascriverli in alcun campo.
Trascrivi i valori e rispondi SOLO con un oggetto JSON esattamente così (usa null per i valori assenti o illeggibili; numeri con il punto decimale, senza unità):
{"height_cm":null,"age":null,"sex":null,
"weight_kg":null,"smm_kg":null,"bfm_kg":null,"pbf_pct":null,"bmi":null,"tbw_l":null,"protein_kg":null,"minerals_kg":null,
"score":null,"vfl":null,"whr":null,"ffm_kg":null,"bmr_kcal":null,"reco_kcal":null,"obesity_deg_pct":null,"target_weight_kg":null,
"seg_lean_pct":{"ra":null,"la":null,"tr":null,"rl":null,"ll":null},
"seg_fat_pct":{"ra":null,"la":null,"tr":null,"rl":null,"ll":null},
"energy":[["nome sport", kcal], ...]}
Indicazioni: "sex" = "M" o "F". "score" = Punteggio InBody (numero prima di /100). "vfl" = Livello Grasso Viscerale. "whr" = Relazione Cintura Fianchi. "ffm_kg" = Massa Magra. "bmr_kcal" = Tasso Metabolico Basale. "reco_kcal" = Assunzione calorica consigliata. "obesity_deg_pct" = Grado di obesità.
"seg_lean_pct"/"seg_fat_pct": le percentuali dell'analisi segmentale (ra/la = braccio destro/sinistro, rl/ll = gamba destra/sinistra, tr = tronco; nel referto le colonne sono Sinistro/Destro).
"energy": la tabella "Dispendio d'energia per esercizio" — ogni sport con le sue kcal (per 30 minuti), nell'ordine in cui compaiono.`;

export function foodPrompt(data) {
  return `Sei un educatore alimentare. Sulla base dei dati di una analisi della composizione corporea (BIA) e dei gusti della persona, scrivi consigli alimentari DIDATTICI in italiano (non una dieta medica: niente grammature rigide per pasto, niente diagnosi).
DATI BIA (documento anonimo): ${JSON.stringify(data.bia || {})}
GUSTI E ABITUDINI dichiarati: ${JSON.stringify(data.gusti || {})}
Tieni conto dei gusti (valorizza ciò che piace, proponi alternative concrete a ciò che va limitato) e delle abitudini dichiarate (es. se salta la colazione, spiega come reintrodurla gradualmente).
Rispondi SOLO con JSON: {"premessa": "2-3 frasi sul quadro generale di questa persona", "privilegiare": [{"cosa":"alimento o gruppo","perche":"motivo legato ai SUOI dati o gusti"}, ... 4-6 voci], "limitare": [{"cosa":"...","perche":"..."} , ... 3-5 voci], "quantita": ["indicazione pratica e misurabile (porzioni a settimana, bicchieri, cucchiai...)", ... 4-6 voci]}`;
}

export function movePrompt(data) {
  return `Sei un educatore motorio. Proponi un percorso di movimento DIDATTICO (non un programma medico) in italiano per questa persona.
DATI BIA (documento anonimo): ${JSON.stringify(data.bia || {})}
GUSTI, MOMENTI DISPONIBILI E LUOGO: ${JSON.stringify(data.gusti || {})}
Crea TRE opzioni alternative: (1) dedicarsi a un solo sport scelto tra quelli che ama o vorrebbe provare, con progressione settimanale; (2) un mix di 2-3 attività diverse nella settimana; (3) movimento nel tempo libero senza sport strutturato (spostamenti attivi, scale, camminate).
Rispetta i momenti dichiarati (giorni/orari) e cita opportunità plausibili del territorio indicato (piste ciclabili, lungomare, sentieri, piscine, impianti — se conosci la zona, nomina luoghi reali; altrimenti resta generico).
Rispondi SOLO con JSON: {"opzioni":[{"titolo":"nome breve","descrizione":"2 frasi","settimana":[{"giorno":"Lun","attivita":"cosa e dove","durata":"45 min"}, ...solo i giorni attivi],"kcal_settimana":numero stimato}, {..}, {..}],"territorio":["2-4 suggerimenti legati alla zona indicata"]}`;
}

// Lettura tollerante del JSON dalla risposta del modello (fence o testo attorno).
export function tolerantJson(text) {
  if (typeof text !== "string") throw new Error("risposta vuota");
  try { return JSON.parse(text); } catch {}
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) { try { return JSON.parse(fence[1]); } catch {} }
  const a = text.indexOf("{"), b = text.lastIndexOf("}");
  if (a >= 0 && b > a) return JSON.parse(text.slice(a, b + 1));
  throw new Error("nessun JSON nella risposta");
}

// ---- provider: Anthropic (Claude) — Messages API, HTTP puro ----
async function callAnthropic(env, prompt, imagesB64) {
  const content = (imagesB64 || []).map(data => ({
    type: "image",
    source: { type: "base64", media_type: "image/jpeg", data },
  }));
  content.push({ type: "text", text: prompt });
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": env.API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: env.MODEL || "claude-opus-5",
      max_tokens: 8000,
      messages: [{ role: "user", content }],
    }),
  });
  if (!res.ok) throw httpError(res.status, await safeText(res));
  const msg = await res.json();
  if (msg.stop_reason === "refusal") throw httpError(422, "richiesta rifiutata dal modello");
  const text = (msg.content || []).filter(b => b.type === "text").map(b => b.text).join("\n");
  return tolerantJson(text);
}

// ---- provider: OpenAI (ChatGPT) — Chat Completions, HTTP puro ----
async function callOpenAI(env, prompt, imagesB64) {
  const content = (imagesB64 || []).map(data => ({
    type: "image_url",
    image_url: { url: "data:image/jpeg;base64," + data },
  }));
  content.push({ type: "text", text: prompt });
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      authorization: "Bearer " + env.API_KEY,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: env.MODEL || "gpt-4o",
      max_tokens: 8000,
      response_format: { type: "json_object" },
      messages: [{ role: "user", content }],
    }),
  });
  if (!res.ok) throw httpError(res.status, await safeText(res));
  const msg = await res.json();
  return tolerantJson(msg.choices?.[0]?.message?.content || "");
}

// ---- provider: mock — per collaudo senza chiave ----
function callMock(kind) {
  if (kind === "extract") return {
    height_cm: 165, age: 45, sex: "F", weight_kg: 78.4, smm_kg: 24.1, bfm_kg: 31.2,
    pbf_pct: 39.8, bmi: 28.8, tbw_l: 34.5, protein_kg: 9.2, minerals_kg: 3.34,
    score: 62, vfl: 12, whr: 0.92, ffm_kg: 47.2, bmr_kcal: 1387, reco_kcal: 1800,
    obesity_deg_pct: 131, target_weight_kg: 62,
    seg_lean_pct: { ra: 80.1, la: 78.2, tr: 88.4, rl: 81.9, ll: 80.6 },
    seg_fat_pct: { ra: 190.5, la: 192.0, tr: 166.2, rl: 156.1, ll: 154.8 },
    energy: [["Camminata", 157], ["Bicicletta", 235], ["Nuoto", 274]],
  };
  if (kind === "food") return {
    premessa: "(Risposta di prova del server mock.) Quadro con massa grassa oltre il range e buona base da cui partire.",
    privilegiare: [{ cosa: "Verdura a ogni pasto", perche: "aumenta sazietà con poche calorie" }, { cosa: "Pesce e legumi", perche: "proteine per proteggere il muscolo" }],
    limitare: [{ cosa: "Bibite zuccherate", perche: "calorie senza sazietà" }],
    quantita: ["Dolci: 1-2 volte a settimana", "Acqua: 6-8 bicchieri al giorno"],
  };
  return {
    opzioni: [
      { titolo: "Camminata progressiva", descrizione: "(Prova mock.) Un solo sport, costanza prima di tutto.", settimana: [{ giorno: "Lun", attivita: "camminata veloce", durata: "30 min" }, { giorno: "Gio", attivita: "camminata veloce", durata: "40 min" }], kcal_settimana: 700 },
      { titolo: "Mix leggero", descrizione: "Alternanza per non annoiarsi.", settimana: [{ giorno: "Mar", attivita: "nuoto", durata: "30 min" }, { giorno: "Sab", attivita: "bicicletta", durata: "60 min" }], kcal_settimana: 900 },
      { titolo: "Tempo libero attivo", descrizione: "Movimento senza sport strutturato.", settimana: [{ giorno: "Ogni giorno", attivita: "scale + spostamenti a piedi", durata: "20 min" }], kcal_settimana: 600 },
    ],
    territorio: ["Percorsi pedonali della zona", "Piscina comunale più vicina"],
  };
}

function httpError(status, message) { const e = new Error(String(status) + ": " + (message || "(nessun dettaglio)")); e.status = status; return e; }
async function safeText(res) { try { return (await res.text()).slice(0, 400); } catch (e) { return "text-err " + e.message; } }

// API pubblica del modulo: due operazioni, indipendenti dal provider.
export async function extract(env, imagesB64) {
  if (!Array.isArray(imagesB64) || imagesB64.length < 1 || imagesB64.length > 3) throw httpError(400, "servono 1-3 immagini");
  for (const s of imagesB64) if (typeof s !== "string" || s.length > 3_000_000) throw httpError(400, "immagine non valida o troppo grande");
  const p = (env.PROVIDER || (env.API_KEY ? "anthropic" : "mock")).toLowerCase();
  if (p === "mock") return callMock("extract");
  if (p === "openai") return callOpenAI(env, EXTRACT_PROMPT, imagesB64);
  return callAnthropic(env, EXTRACT_PROMPT, imagesB64);
}

export async function advise(env, kind, data) {
  if (kind !== "food" && kind !== "move") throw httpError(400, "kind non valido");
  if (JSON.stringify(data || {}).length > 20_000) throw httpError(400, "dati troppo grandi");
  const prompt = kind === "food" ? foodPrompt(data || {}) : movePrompt(data || {});
  const p = (env.PROVIDER || (env.API_KEY ? "anthropic" : "mock")).toLowerCase();
  if (p === "mock") return callMock(kind);
  if (p === "openai") return callOpenAI(env, prompt);
  return callAnthropic(env, prompt);
}
