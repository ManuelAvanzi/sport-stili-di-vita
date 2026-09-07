# -*- coding: utf-8 -*-
"""Genera referti InBody fac-simile (dati inventati) nello stesso formato
tecnico dei PDF LookinBody Mac: una pagina A4 con un'unica immagine JPEG."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 2480, 3512
RED = (155, 27, 33)
INK = (25, 25, 25)
GREY = (110, 110, 110)
LGREY = (200, 200, 200)
BARBG = (225, 225, 225)
BARFG = (60, 60, 60)
ZONE = (170, 170, 170)

F = "C:/Windows/Fonts/"
def font(name, size):
    return ImageFont.truetype(F + name, size)

fH1   = font("timesbd.ttf", 64)     # titoli sezione (serif bold, come l'originale)
fLogo = font("arialbd.ttf", 110)
fTag  = font("arial.ttf", 44)
fLbl  = font("arial.ttf", 40)
fLblB = font("arialbd.ttf", 42)
fVal  = font("arialbd.ttf", 52)
fBig  = font("timesbd.ttf", 130)
fMid  = font("arialbd.ttf", 46)
fSm   = font("arial.ttf", 34)
fSmB  = font("arialbd.ttf", 36)

def make_report(d):
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    M = 95

    # ---------- header ----------
    dr.text((M, 60), "InBody", font=fLogo, fill=RED)
    dr.text((1620, 130), "[InBody270]", font=fTag, fill=INK)
    dr.rectangle([M, 210, W-M, 222], fill=RED)
    # anagrafica
    y0, y1 = 240, 360
    cols = [M, 560, 1000, 1280, 1560, 2385]
    heads = ["ID", "Altezza", "Età", "Genere", "Data Test / Ora"]
    vals  = [d["id"], f"{d['h']}cm", str(d["eta"]), d["gen"], d["data"]]
    dr.rectangle([M, y0, W-M, y1], outline=LGREY, width=3)
    for i, (hd, vv) in enumerate(zip(heads, vals)):
        if i: dr.line([cols[i], y0, cols[i], y1], fill=LGREY, width=3)
        dr.text((cols[i]+22, y0+12), hd, font=fLbl, fill=GREY)
        dr.text((cols[i]+22, y0+62), vv, font=fVal, fill=INK)

    LX, LW = M, 1420          # colonna sinistra
    RX = 1600                 # colonna destra

    # ---------- sx: composizione corporea ----------
    y = 460
    dr.text((LX, y), "Analisi della Composizione Corporea", font=fH1, fill=INK); y += 100
    comp = [
        ("Acqua Corporea Totale", "(L)",  d["tbw"],  d["r_tbw"]),
        ("Proteine",              "(kg)", d["prot"], d["r_prot"]),
        ("Minerali",              "(kg)", d["min"],  d["r_min"]),
        ("Massa Grassa del Corpo","(kg)", d["bfm"],  d["r_bfm"]),
        ("Peso",                  "(kg)", d["peso"], d["r_peso"]),
    ]
    for i, (lbl, unit, v, rng) in enumerate(comp):
        ry = y + i*96
        if i % 2 == 0:
            dr.rectangle([LX, ry-8, LX+LW, ry+80], fill=(243,243,243))
        dr.text((LX+16, ry+8), lbl, font=fLblB, fill=INK)
        dr.text((LX+620, ry+14), unit, font=fSm, fill=GREY)
        dr.text((LX+760, ry+2), f"{v}", font=fVal, fill=INK)
        dr.text((LX+960, ry+14), f"(  {rng[0]}~{rng[1]}  )", font=fLbl, fill=GREY)
    y += len(comp)*96 + 70

    # ---------- sx: muscolo-grasso (barre) ----------
    dr.text((LX, y), "Analisi Muscolo - Grasso", font=fH1, fill=INK); y += 95
    def bar_row(y, lbl, unit, v, frac):
        dr.text((LX+16, y+6), lbl, font=fLblB, fill=INK)
        dr.text((LX+16, y+56), unit, font=fSm, fill=GREY)
        bx0, bx1 = LX+420, LX+LW
        dr.rectangle([bx0, y+14, bx1, y+58], fill=BARBG)
        dr.rectangle([bx0+(bx1-bx0)*0.28, y+14, bx0+(bx1-bx0)*0.52, y+58], fill=ZONE)
        fw = max(0.04, min(0.97, frac))
        dr.rectangle([bx0, y+20, bx0+(bx1-bx0)*fw, y+52], fill=BARFG)
        dr.text((bx0+(bx1-bx0)*fw+14, y+10), f"{v}", font=fVal, fill=INK)
    bar_row(y,      "Peso", "(kg)", d["peso"], d["f_peso"])
    bar_row(y+110,  "Massa del\nMuscolo Scheletrico", "(kg)", d["smm"], d["f_smm"])
    bar_row(y+220,  "Massa Grassa\ndel Corpo", "(kg)", d["bfm"], d["f_bfm"])
    y += 330 + 70

    # ---------- sx: obesità ----------
    dr.text((LX, y), "Analisi dell'obesità", font=fH1, fill=INK); y += 95
    dr.text((LX+16, y+6), "IMC", font=fLblB, fill=INK)
    dr.text((LX+16, y+56), "Indice di Massa Corporea  (kg/m²)", font=fSm, fill=GREY)
    bar_row(y, "", "", "", 0)  # sfondo barra vuota per IMC
    bx0, bx1 = LX+420, LX+LW
    dr.rectangle([bx0, y+14, bx1, y+58], fill=BARBG)
    dr.rectangle([bx0+(bx1-bx0)*0.24, y+14, bx0+(bx1-bx0)*0.42, y+58], fill=ZONE)
    fw = max(0.04, min(0.97, d["f_imc"]))
    dr.rectangle([bx0, y+20, bx0+(bx1-bx0)*fw, y+52], fill=BARFG)
    dr.text((bx0+(bx1-bx0)*fw+14, y+10), f"{d['imc']}", font=fVal, fill=INK)
    y2 = y + 120
    dr.text((LX+16, y2+6), "Percentuale di", font=fLblB, fill=INK)
    dr.text((LX+16, y2+52), "Grasso Corporeo  (%)", font=fSmB, fill=INK)
    dr.rectangle([bx0, y2+14, bx1, y2+58], fill=BARBG)
    dr.rectangle([bx0+(bx1-bx0)*0.22, y2+14, bx0+(bx1-bx0)*0.40, y2+58], fill=ZONE)
    fw = max(0.04, min(0.97, d["f_pbf"]))
    dr.rectangle([bx0, y2+20, bx0+(bx1-bx0)*fw, y2+52], fill=BARFG)
    dr.text((bx0+(bx1-bx0)*fw+14, y2+10), f"{d['pbf']}", font=fVal, fill=INK)
    y = y2 + 160

    # ---------- sx: segmentale ----------
    dr.text((LX, y), "Analisi Massa Magra e Grassa Segmentale", font=fH1, fill=INK); y += 95
    seg_rows = ["Braccio Sinistro", "Braccio Destro", "Tronco", "Gamba Sinistra", "Gamba Destra"]
    dr.text((LX+420, y), "Massa Magra", font=fSmB, fill=INK)
    dr.text((LX+900, y), "Massa Grassa", font=fSmB, fill=INK)
    y += 56
    for i, name in enumerate(seg_rows):
        ry = y + i*74
        if i % 2 == 0:
            dr.rectangle([LX, ry-6, LX+LW, ry+60], fill=(243,243,243))
        L = d["seg_lean"][i]; Fg = d["seg_fat"][i]
        dr.text((LX+16, ry+8), name, font=fLbl, fill=INK)
        dr.text((LX+420, ry+2), f"{L[0]} kg", font=fMid, fill=INK)
        dr.text((LX+650, ry+12), f"{L[1]}%", font=fLbl, fill=GREY)
        dr.text((LX+900, ry+2), f"{Fg[0]} kg", font=fMid, fill=INK)
        dr.text((LX+1130, ry+12), f"{Fg[1]}%", font=fLbl, fill=GREY)
    y += 5*74 + 80

    # ---------- sx: storia ----------
    dr.text((LX, y), "Storia della Composizione Corporea", font=fH1, fill=INK); y += 100
    hist = d["storia"]
    n = len(hist)
    colw = LW // (n + 1)
    rows = [("Peso", "(kg)", 1), ("Massa del\nMuscolo Scheletrico", "(kg)", 2), ("Percentuale di\nGrasso Corporeo", "(%)", 3)]
    for rI, (lbl, unit, idx) in enumerate(rows):
        ry = y + rI*120
        dr.rectangle([LX, ry-6, LX+340, ry+100], fill=(238,238,238))
        dr.text((LX+14, ry+6), lbl, font=fSmB, fill=INK)
        dr.text((LX+14, ry+58 if "\n" not in lbl else ry+94-28), unit, font=fSm, fill=GREY)
        for cI, hrow in enumerate(hist):
            cx = LX + 340 + 30 + cI*colw
            dr.text((cx, ry+14), f"{hrow[idx]}", font=fMid, fill=INK)
    ry = y + 3*120
    for cI, hrow in enumerate(hist):
        cx = LX + 340 + 30 + cI*colw
        dr.text((cx, ry), hrow[0].split(" ")[0], font=fSm, fill=GREY)
        dr.text((cx, ry+42), hrow[0].split(" ")[1], font=fSm, fill=GREY)

    # ---------- dx: punteggio ----------
    ry = 460
    dr.text((RX, ry), "Punteggio InBody", font=fH1, fill=INK)
    dr.line([RX+560, ry+40, W-M, ry+40], fill=INK, width=3)
    dr.text((RX+120, ry+80), f"{d['score']}", font=fBig, fill=INK)
    dr.text((RX+120+len(str(d['score']))*72, ry+150), "/100 Punteggio", font=fLbl, fill=INK)
    ry += 300

    # controllo del peso
    dr.text((RX, ry), "Controllo del Peso", font=fH1, fill=INK); ry += 90
    for lbl, v in [("Peso Target", f"{d['target']}  kg"), ("Controllo del Peso", f"{d['ctrl_peso']}  kg"),
                   ("Controllo del Grasso", f"{d['ctrl_grasso']}  kg"), ("Controllo del Muscolo", f"{d['ctrl_musc']}  kg")]:
        dr.text((RX, ry), lbl, font=fLbl, fill=INK)
        dr.text((RX+520, ry-4), v, font=fMid, fill=INK)
        ry += 64
    ry += 30

    # cintura fianchi + viscerale
    dr.text((RX, ry), "Relazione Cintura Fianchi", font=fH1, fill=INK); ry += 86
    dr.text((RX+60, ry), f"{d['whr']}", font=fVal, fill=INK); ry += 90
    dr.text((RX, ry), "Livello Grasso Viscerale", font=fH1, fill=INK); ry += 86
    dr.text((RX+60, ry), f"Livello    {d['vfl']}", font=fVal, fill=INK); ry += 100

    # parametri di ricerca
    dr.text((RX, ry), "Parametri di Ricerca", font=fH1, fill=INK); ry += 90
    ricerca = [
        ("Massa Magra", f"{d['ffm']}  kg", f"(  {d['r_ffm'][0]}~{d['r_ffm'][1]}  )"),
        ("Tasso Metabolico Basale", f"{d['bmr']}  kcal", f"(  {d['r_bmr'][0]}~{d['r_bmr'][1]}  )"),
        ("Grado di obesità", f"{d['grado']}  %", "(  90~110  )"),
        ("SMI", f"{d['smi']}  kg/m²", ""),
        ("Assunzione calorica consigliata", f"{d['kcal']}  kcal", ""),
    ]
    for lbl, v, rng in ricerca:
        dr.text((RX, ry), lbl, font=fLbl, fill=INK)
        dr.text((RX+560, ry-4), v, font=fMid, fill=INK)
        if rng: dr.text((RX+560, ry+52), rng, font=fSm, fill=GREY)
        ry += 64 + (44 if rng else 0)
    ry += 30

    # dispendio energia
    dr.text((RX, ry), "Dispendio d'energia per esercizio", font=fH1, fill=INK); ry += 84
    en = d["energy"]
    half = (len(en)+1)//2
    for i, (sp, kc) in enumerate(en):
        cx = RX if i < half else RX + 420
        cy = ry + (i % half)*54
        dr.text((cx, cy), sp, font=fSm, fill=INK)
        dr.text((cx+300, cy), str(kc), font=fSmB, fill=INK)
    ry += half*54 + 20
    dr.text((RX, ry), "* In base al proprio peso attuale, durata 30 minuti", font=fSm, fill=GREY); ry += 70

    # impedenza
    dr.text((RX, ry), "Impedenza", font=fH1, fill=INK); ry += 80
    dr.text((RX+250, ry), "BD", font=fSmB, fill=INK)
    for i, hd in enumerate(["BD","BS","TR","GD","GS"]):
        dr.text((RX+250+i*115, ry), hd, font=fSmB, fill=INK)
    ry += 48
    dr.text((RX, ry), "Z(Ω)  20 kHz", font=fSm, fill=INK)
    for i, v in enumerate(d["imp20"]):
        dr.text((RX+250+i*115, ry), f"{v}", font=fSm, fill=INK)
    ry += 46
    dr.text((RX+62, ry), "100 kHz", font=fSm, fill=INK)
    for i, v in enumerate(d["imp100"]):
        dr.text((RX+250+i*115, ry), f"{v}", font=fSm, fill=INK)

    # footer
    dr.rectangle([M, H-150, W-M, H-142], fill=RED)
    dr.text((M, H-120), f"Ver.LB120 Mac.2.0.0.1 - FAC-SIMILE PER COLLAUDO (dati inventati)", font=fSm, fill=GREY)
    dr.text((1500, H-120), "Copyright 1996~ by InBody Co., Ltd. All rights reserved.", font=fSm, fill=GREY)
    return im

# ------------------------------------------------------------------
SOGGETTI = [
    dict(  # donna 45 anni, sovrappeso
        id="260905-02", h="165.0", eta=45, gen="Femmina", data="05.09.2026 10:24",
        tbw=34.5, r_tbw=(29.3,35.8), prot=9.2, r_prot=(7.8,9.6), min=3.34, r_min=(2.81,3.43),
        bfm=31.2, r_bfm=(14.1,22.5), peso=78.4, r_peso=(48.2,65.2),
        smm=24.1, imc=28.8, pbf=39.8,
        f_peso=.62, f_smm=.30, f_bfm=.78, f_imc=.58, f_pbf=.74,
        score=62, target=62.0, ctrl_peso=-16.4, ctrl_grasso=-18.6, ctrl_musc=2.2,
        whr=0.92, vfl=12, ffm=47.2, r_ffm=(37.4,45.7), bmr=1387, r_bmr=(1244,1436),
        grado=131, smi=5.9, kcal=1800,
        seg_lean=[(1.9,78.2),(2.0,80.1),(21.5,88.4),(6.2,80.6),(6.3,81.9)],
        seg_fat=[(2.9,192.0),(2.9,190.5),(15.8,166.2),(4.6,154.8),(4.6,156.1)],
        imp20=(322.4,325.0,24.1,291.6,294.2), imp100=(275.8,278.1,19.0,249.3,251.6),
        storia=[("26.03.10 09:50",80.1,24.3,41.0),("26.05.06 11:12",79.5,24.2,40.6),
                ("26.07.01 10:05",78.9,24.1,40.1),("26.09.05 10:24",78.4,24.1,39.8)],
    ),
    dict(  # uomo 62 anni, normopeso con poco muscolo
        id="260905-07", h="172.0", eta=62, gen="Maschio", data="05.09.2026 16:41",
        tbw=37.6, r_tbw=(36.5,44.7), prot=10.1, r_prot=(9.9,12.1), min=3.62, r_min=(3.46,4.22),
        bfm=18.9, r_bfm=(10.8,17.3), peso=70.2, r_peso=(55.4,74.9),
        smm=27.8, imc=23.7, pbf=26.9,
        f_peso=.44, f_smm=.34, f_bfm=.56, f_imc=.40, f_pbf=.55,
        score=71, target=67.5, ctrl_peso=-2.7, ctrl_grasso=-4.8, ctrl_musc=2.1,
        whr=0.90, vfl=11, ffm=51.3, r_ffm=(49.8,60.9), bmr=1477, r_bmr=(1520,1758),
        grado=103, smi=6.9, kcal=2200,
        seg_lean=[(2.6,91.8),(2.6,92.4),(23.4,95.2),(7.4,86.0),(7.4,86.8)],
        seg_fat=[(1.1,121.4),(1.1,119.8),(9.8,136.0),(2.7,117.5),(2.7,118.9)],
        imp20=(281.2,283.5,21.6,258.4,260.0), imp100=(240.6,242.4,17.1,221.0,222.4),
        storia=[("26.04.18 15:30",71.0,28.1,27.5),("26.06.25 17:02",70.6,27.9,27.2),
                ("26.09.05 16:41",70.2,27.8,26.9)],
    ),
    dict(  # ragazza 22 anni, atletica
        id="260906-11", h="170.0", eta=22, gen="Femmina", data="06.09.2026 18:05",
        tbw=35.7, r_tbw=(31.2,38.2), prot=9.6, r_prot=(8.4,10.3), min=3.41, r_min=(3.02,3.69),
        bfm=12.8, r_bfm=(12.0,19.2), peso=61.5, r_peso=(51.2,69.3),
        smm=27.9, imc=21.3, pbf=20.8,
        f_peso=.38, f_smm=.46, f_bfm=.30, f_imc=.33, f_pbf=.36,
        score=82, target=61.5, ctrl_peso=0.0, ctrl_grasso=0.0, ctrl_musc=0.0,
        whr=0.74, vfl=3, ffm=48.7, r_ffm=(39.9,48.8), bmr=1422, r_bmr=(1319,1523),
        grado=98, smi=6.6, kcal=2000,
        seg_lean=[(2.3,101.6),(2.3,102.2),(22.0,103.0),(7.6,107.4),(7.6,108.1)],
        seg_fat=[(0.9,96.0),(0.9,94.7),(5.4,90.2),(2.3,97.5),(2.3,98.3)],
        imp20=(298.0,300.2,22.4,270.1,272.5), imp100=(254.9,256.7,17.8,231.0,233.0),
        storia=[("26.01.15 18:20",63.2,27.2,23.5),("26.03.02 19:01",62.8,27.4,22.9),
                ("26.05.11 18:44",62.2,27.6,22.0),("26.07.07 18:30",61.8,27.8,21.3),
                ("26.09.06 18:05",61.5,27.9,20.8)],
    ),
]

BASE_ENERGY = [("Golf",142),("Camminata",161),("Yoga",161),("Tennis",242),("Bicicletta",242),
               ("Boxe",242),("Basket",242),("Escursionismo",263),("Aerobica",282),("Jogging",282),
               ("Calcio",282),("Nuoto",282),("Squash",403),("Taekwondo",403)]

OUT = r"C:\Users\manue\Desktop\PDF-prova-BIA"
os.makedirs(OUT, exist_ok=True)
names = ["BIA 2101.pdf", "BIA 3407.pdf", "BIA 5512.pdf"]
for d, name in zip(SOGGETTI, names):
    d["energy"] = [(sp, round(kc * d["peso"] / 80.6)) for sp, kc in BASE_ENERGY]
    im = make_report(d)
    path = os.path.join(OUT, name)
    im.save(path, "PDF", resolution=300.0, quality=88)
    raw = open(path, "rb").read()
    has_jpeg = b"\xff\xd8\xff" in raw
    print(name, round(len(raw)/1024), "KB | JPEG dentro:", has_jpeg)
    im.resize((im.width//4, im.height//4)).save(os.path.join(OUT, name.replace(".pdf", "_anteprima.png")))
print("OK ->", OUT)
