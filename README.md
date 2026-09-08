# Sport e Stili di Vita

App web didattica in 4 tappe che parte dai dati di una BIA (bilancia bioimpedenziometrica
InBody) per proporre consigli alimentari e attività motorie personalizzati.
Basata sul documento descrittivo "SPORT E STILI DI VITA" (G. Carraro, settembre 2026).

## Le 4 tappe

1. **Benessere e BIA** — introduzione didattica (skippabile): composizione corporea,
   calcolatore del peso consigliato (IMC), come funziona la bioimpedenziometria, glossario.
2. **Carica i dati** — upload del PDF prodotto dalla BIA + questionario su gusti, luogo,
   abitudini alimentari e momenti di movimento. Anonimizzazione: nomi mai trascritti,
   documento identificato da un codice casuale a 4 cifre. I dati restano nel browser.
3. **Mangia meglio** — distribuzione delle calorie sui pasti (dal fabbisogno del referto),
   consigli personalizzati generati con AI, menu per il turismo sportivo (cicloturisti,
   arrampicatori, nuotatori, subacquei, trekking).
4. **Attività sportive** — dispendio energetico per sport (dal referto), piano di movimento
   in tre varianti generato con AI tenendo conto di gusti, momenti disponibili e territorio.

## File

| File            | Cosa è |
|-----------------|--------|
| `index.html`    | Pagina completa standalone: è il file servito online (GitHub Pages o qualsiasi hosting statico). |
| `artifact.html` | Stesso sorgente nel formato Artifact di claude.ai (senza doctype/head: il wrapper lo aggiunge la piattaforma). |
| `test-data/`    | Tre referti InBody **fac-simile** (dati inventati, footer "FAC-SIMILE PER COLLAUDO"), le anteprime PNG e lo script che li genera. |

`index.html` e `artifact.html` condividono il contenuto: quando si modifica uno,
rigenerare l'altro (index = artifact + wrapper `<!doctype html><html><head>…`).

## Come funziona la lettura dei PDF

I PDF esportati da LookinBody (Mac) sono una pagina A4 con dentro **un'unica immagine
JPEG** e nessun testo. La pagina non usa pdf.js: cerca nei byte del PDF lo span JPEG
più grande (marker `FFD8FF…FFD9`), lo carica come immagine e la taglia in due metà
ad alta risoluzione da passare all'AI. Zero dipendenze, ~300 ms.

## Dove funziona l'AI

L'estrazione automatica dei valori e la generazione dei consigli usano il runtime
`window.claude` (capability `sample`), disponibile **solo quando la pagina è aperta
come Artifact su claude.ai**: ogni visitatore usa il proprio account Claude e
autorizza al primo utilizzo.

**Per attivare l'AI sul sito pubblico** c'è il backend in `server/` (vedi
`server/README.md`): un proxy con la chiave API dove il provider è intercambiabile
(Claude o ChatGPT cambiando `PROVIDER` e `API_KEY`). Una volta deployato, basta
mettere il suo URL in `window.SVS_API` dentro `index.html`.

Senza backend, sulla versione online statica la pagina degrada da sola: l'upload del
referto mostra l'anteprima e invita all'inserimento manuale; le tappe 3 e 4 mostrano i
contenuti didattici e i calcoli non-AI. Il backend di `server/` è esattamente quel pezzo:
la chiave resta sul server, mai nel client.

## Deploy

- **Artifact claude.ai** (AI attiva): https://claude.ai/code/artifact/fe3e5f46-4390-4530-8074-0d356ee3693b
- **GitHub Pages**: Settings → Pages → Deploy from branch → `main` / root. Il sito è `index.html`.

## Test

Trascinare uno dei PDF di `test-data/` nella tappa 2 e confrontare i valori estratti
con le anteprime `*_anteprima.png` (istruzioni complete in `test-data/LEGGIMI.txt`).
