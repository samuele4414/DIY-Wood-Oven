# C02 — architettura preliminare del forno due pizze

Estensione separata dello studio C01. Nessun file V4, C01, MATLAB o CFD
precedente viene cambiato. Sorgenti Python senza dipendenze esterne;
le fonti produttori consultate sono archiviate in `fonti/`.

## Aprire la consegna

- `output/index.html`: scheda offline, 4 tavole SVG e sintesi materiali/gate.
- `output/Scheda_C02.pdf`: sintesi A4 orizzontale di 6 pagine.
- `output/rapporto.html` / `output/RAPPORTO_C02.md`: rapporto completo con
  ipotesi, calcoli, materiali/fonti e limiti (più esteso della scheda PDF).
- `output/calcoli_C02.json` / `output/rete_pressione.csv`: screening meccanico,
  ingombri, passaggi e 25 righe di confronto della rete 1D (inclusi richiami).
- `output/distinta_preliminare.csv` / `output/materiali_C02.json`: gruppi
  funzionali e materiali/fonti; nessun codice ordinabile, metrature aperte.
  CSV con separatore `;`, numeri della rete con punto decimale, UTF-8 con BOM.
- `output/richieste_fornitori.html` / `RICHIESTE_FORNITORI.md`: bozze tecniche;
  nessun fornitore contattato, nessun acquisto autorizzato.
- `output/piano_banco.html` / `PIANO_BANCO_C02.md`: gate componenti, montaggio
  a freddo, campione caldo e criteri da fissare prima delle prove.

PDF e PNG sono anteprime browser, non nuovi render fotorealistici o CAD.
I disegni sono SCHEMI e riserve, non file costruttivi/taglio.

## Rigenerare dalla radice del progetto

```powershell
python -B v4/architettura_c02/build_study.py
python -B -m unittest discover -s v4/architettura_c02 -p "test_*.py" -v
powershell -NoProfile -ExecutionPolicy Bypass -File v4/architettura_c02/export_preview.ps1
```

Il generatore scrive soltanto i propri artefatti noti in `output/`; non
elimina altre cartelle/file. Esportare PDF/PNG **dopo ogni rigenerazione**:
non vengono aggiornati dal solo comando Python. `esportazione.json` registra
hash dei file HTML/SVG usati dal browser e delle anteprime prodotte.
L'esportatore usa un profilo temporaneo isolato sotto
`C:\Users\samue\AppData\Local\Temp\opencode`, senza toccare sessioni browser.

`provenienza.json` registra hash delle fonti, dei sorgenti e il numero di test:
sono verifiche di software/coerenza, non prove sul forno.
`checks.py` usa il generatore geometrico C01 in sola lettura per il budget
del corpo, e riproduce la rete MATLAB aggiungendo sensitività della presa.
Non collega le prestazioni CFD 30/50 alla proposta pietra 20/isolamento 75.

## Proposta e punti aperti

- Motori laterali, 2 moduli indipendenti 240 × 180; vano 160 netti e carrier
  riservato 15. Corpo circa 965 × 915 × 671 mm, piedini inclusi e **collare/camino/
  raccordi esclusi**. Nuovo collare/collettore non integrati in CAD.
- Presa 90 cm² NETTI è un punto di confronto, non un dimensionamento approvato.
  Rete favorevole +2,23 Pa; caso T150 °C/K8/vento 3 Pa: −5,04 Pa; porta aperta critica.
  Nessuna nuova CFD, prova fisica, combustione/CO o temperatura esterna calcolata.
- Collo 170 × 90 candidato per Ø130, non Ø150; collare superiore 260 ESTERNI,
  base 440 tra facce da integrare. La base 340 non contiene il budget prudenziale
  della piastra rettangolare nell'ottagono; 440 sporge 7,5 davanti alla pelle C01.
- Pietra flottante, appoggi portanti distinti dall'isolante, cartuccia distinta
  dal riduttore: componenti, tolleranze, limiti termici e manutenzione da verificare.
- Shortlist 310S/253 MA, WM970 SW e famiglia PROMASIL, più sistema camino reale;
  dati documentati distinti dalle ipotesi e dai prodotti non ancora selezionati.

Preriscaldamento 45–60 min, cottura, sicurezza e durata non dimostrati.
Prossimo passo operativo: CAD/schede reali e montaggio a freddo di un modulo;
campione caldo/prototipo solo dopo dimensionamento e riesame tecnico.
