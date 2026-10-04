# C01 — ingombro tecnico del concept inox sfaccettato

**Studio preliminare, non esecutivo.** Non sono file da mandare al taglio o in
produzione. Nessuna CFD, verifica strutturale o prova fisica nuova.

## Aprire la consegna

- [Visualizzatore 3D e tavole offline](output/index.html)
- [Scheda PDF](output/Scheda_C01.pdf), se esportata con Chrome/Edge
- [Rapporto tecnico](output/RAPPORTO_C01.md)
- [Piano delle verifiche](output/PIANO_VERIFICHE.md)
- [Pianta](output/pianta.svg)
- [Sezione trasversale](output/sezione_trasversale.svg)
- [Sezione longitudinale](output/sezione_longitudinale.svg)

Il visualizzatore HTML si apre direttamente con un browser; non richiede
server, CDN, connessione, WebGL o pacchetti Python. Trascinare per ruotare,
rotella per zoomare. Sono disponibili nove scenari d'ingombro e due altezze
candidate della canna. Le tavole 2D rappresentano la baseline, non lo
scenario momentaneamente selezionato nella vista 3D.

## Requisiti confermati e ipotesi

Confermati: domestico outdoor, appoggio fisso, due pizze Ø300, cottura
indicativa 60–90 s, preriscaldamento desiderato 45–60 min. Sono obiettivi.
Stile: inox satinato, pannelli piani sfaccettati, bocca/base nere.

La camera deriva da `../quote_v4.json`, che **non viene modificato**.
Le nuove ipotesi sono in `concept.json`, separando pietra piano 20 mm,
focolare 30 mm, isolante corpo 75 mm, riserva montaggio 10 mm e vano
meccanico netto 120 mm. Materiali e componenti reali non sono selezionati.

La baseline riserva circa **965 × 915 × 617 mm**, altezza corpo con piedini,
senza camino. Con canna H1000 dal collare: circa 1717 mm dal supporto.
Il camino mantiene l'asse **anteriore V4**: il render estetico lo suggerisce
posteriore, ma un'immagine non autorizza a modificare il percorso dei fumi.

Le falde sono ricavate da piani con distanze **normali** alla camera
parabolica; non si ottengono aggiungendo semplicemente 75 mm in verticale.
La verifica è geometrica, esclude attraversamenti e dettagli locali e non
dimostra una temperatura sicura della scocca. La riserva da 10 mm non è un
gioco termomeccanico approvato.

## Rigenerare

Python 3.11 o successivo, sola libreria standard:

```powershell
python -B v4/concept_sfaccettato/build_study.py
python -B -m unittest discover -s v4/concept_sfaccettato -p "test_*.py" -v
```

Controllo opzionale delle interazioni con Node già installato:

```powershell
node v4/concept_sfaccettato/test_viewer.cjs
```

Questo harness usa un DOM/canvas minimo: verifica selettori e rasterizzatore,
ma non sostituisce il controllo visivo delle anteprime in un browser reale.

Il generatore verifica la geometria prima di esportare e scrive soltanto
nella propria cartella `output`. La rigenerazione sostituisce gli artefatti
generati: salvare altrove eventuali modifiche manuali a quei file.
Modelli MATLAB/Simulink, input CFD, risultati precedenti, quote V4 e immagini
del progetto non vengono sovrascritti. Nessun solver viene avviato.

Esportazione opzionale PDF e PNG con un browser già installato:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File v4/concept_sfaccettato/export_preview.ps1 -IncludeViewer
```

Lo script usa un profilo temporaneo isolato sotto `%LOCALAPPDATA%\Temp\opencode`;
non interviene sul profilo abituale del browser. In alternativa aprire
`output/scheda_stampa.html` e stampare in PDF, formato A3 orizzontale.

## CAD e provenienza

`output/ingombri_C01.dxf` è un riferimento 2D in millimetri con layer separati:
i cerchi sono dischi nominali, **non fori di taglio**. `assieme_C01.obj` con
`.mtl` descrive superfici e volumi riservati in **mm**, non un assieme di
solidi manifatturabili. OBJ non codifica unità: scegliere millimetri in importazione.

`confronto_ingombri.csv` contiene i nove scenari, separatore `;`.
`verifica_geometrica.json` e `test_generatore.log` documentano i soli controlli
numerici/geometrici. `provenienza.json` registra hash di input e artefatti.
PDF/PNG derivano dal browser e non dai campi CFD; sono esclusi dagli hash
del generatore. Il riferimento termico preesistente resta non calibrato.

## Prima di costruire

Definire aria e collettore; scegliere leghe e isolanti con schede reali;
progettare carrier, appoggi, cuscinetti e trasmissione; verificare pala,
sportelli e manutenzione; aggiornare modelli; provare un prototipo
strumentato. Il piano dettagliato è nella consegna.
