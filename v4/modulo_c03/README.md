# C03 — componenti reali e modulo digitale a freddo

Fase separata da C01/C02. Obiettivo: confrontare documenti/CAD pubblici di
componenti commerciali, verificare il layout di un modulo e preparare il
registro del banco a freddo. Nessun ordine, contatto con fornitori o prova
fisica è autorizzato da questi file. Nessuna approvazione per uso a caldo,
alimentare, outdoor o produzione.

Le fonti vengono archiviate in `fonti/`; lo STEP del fornitore e il modello
di inviluppo dello studio restano distinti. Le ricostruzioni semplificate
non sostituiscono verifica CAD, tolleranze, dettagli di montaggio e riesame.

## Aprire la consegna

`output/index.html`: viewer offline del modulo sinistro, scheda di5 pagine,
tavole, rapporto, distinta candidati, richieste non inviate e registro banco
vuoto. `output/Scheda_C03.pdf` è l'esportazione stampabile, non un disegno
costruttivo. Il CAD `cad/modulo_freddo_C03_NON_ESECUTIVO.step` è misto:
1 motore da STEP originale +20 inviluppi, non un modulo completo qualificato.

## Riprodurre dalla radice del progetto

```powershell
python -B v4/modulo_c03/build_study.py
python -B -m unittest discover -s v4/modulo_c03 -p "test_*.py" -v
node v4/modulo_c03/test_viewer.cjs
powershell -NoProfile -ExecutionPolicy Bypass -File v4/modulo_c03/export_preview.ps1
python -B v4/modulo_c03/build_study.py --verify
```

Il build usa solo la libreria standard e rifiuta hash CAD obsoleti. Se
cambiano layout, componenti, geometria o calcoli, ripetere prima l'audit:

```powershell
python -B v4/modulo_c03/audit_cad.py --gmsh-dir "C:\Users\samue\AppData\Local\Temp\opencode\forno-c03-cad"
```

Per questo audit è stato usato Gmsh4.15.2/OCC in una cartella temporanea
isolata; nessuna installazione Python globale. In un altro ambiente fornire
un'installazione/SDK Gmsh della stessa versione con modulo Python e DLL,
oppure usare un ambiente virtuale separato. Il viewer non richiede Gmsh.

PDF/PNG richiedono un export dopo ogni build; un manifest separato verifica
gli ingressi esatti. Fonte SKF acquisita come copia pubblica RS, documenti
proprietari conservati localmente senza pubblicazione/redistribuzione.

## Vincoli ancora aperti

- TDS motore3Nm / curva2Nm; pretensione e100N radiali da chiarire.
- Cassetta136 nel vano160: fit nominale, non tolleranze o montaggio.
- Porta280 × 144 e abbassamento12: solo1/1 residui verticali dopo margini3.
- Carter, guide, giunto, interfaccia calda, ritenzioni, grasso e cablaggi non completati.
- Driver fuori vano (ambiente max40°C); forno caldo e outdoor non qualificati.
