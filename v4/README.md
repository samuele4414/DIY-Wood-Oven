# V4 — base geometrica per il design

Data: 2026-09-21  
Stato: **bozza per design, non esecutiva**.  
Quote in millimetri; origine nel bordo anteriore sinistro del piano di cottura, sulla sua superficie superiore. I dettagli strutturali, l'isolamento e le dimensioni esterne sono ancora da definire.

La [scheda PDF](output/pdf/Forno_V4_Scheda_design.pdf) è la consegna da condividere con la designer. `quote_v4.json` conserva i parametri della V4; `Base_V4_riferimento_mm.dxf` contiene una pianta CAD nominale, in millimetri, con elementi separati per layer. I cerchi delle piastre indicano i dischi, non fori di taglio; camino e collare sono proiezioni dal tetto. Parte da un piano di cottura in cordierite di 790 × 410 mm, con due dischi rotanti Ø320 mm ai centri (210, 205) e (580, 205). La pizza di riferimento e Ø300 mm: i dischi Ø320 non implicano che una pizza Ø320 sia utilizzabile con sufficiente gioco.

## Da conservare nel design

- Il piano 790 × 410 e i due dischi Ø320; i loro centri sono fissati per questa base V4.
- La funzione: due pizze, rotazione, supporti e trasmissione sotto i dischi, accesso pala dalla parte anteriore, legna sul retro e botola posteriore.
- La disposizione funzionale: porta esterna, raccolta fumi alta nella parte anteriore anche sopra le pizze, focolare posteriore.
- La porta non deve chiudere il collegamento tra camera e canna fumaria.

## Il design puo modificare

- La forma interna ed esterna della camera di combustione e della botola posteriore, con nuova verifica di ingombri, fiamma e flussi.
- La volta: profilo, materiale e linguaggio estetico. Le ipotesi da confrontare sono acciaio isolato e refrattario; il profilo candidato ha gronda a z=190 e colmo a z=280.
- La forma esterna, struttura, isolamento, rivestimento, base e finiture. L'inviluppo interno 790 × 740 non e una misura della base esterna.
- La forma del collettore fumi, se mantiene il passaggio libero dei fumi, lo spazio per pala e l'altezza libera sopra le pizze.

## Da ricalcolare se cambiano volta o focolare

- Volume della camera, area e distanza dal fuoco.
- Raccolta fumi, tiraggio, sezione e altezza effettiva della canna.
- Accesso della pala e ingombro della porta.
- Supporti, albero e trasmissione sotto ciascun disco.
- Distribuzione termica, isolamento e dilatazioni dei materiali.

L'avancorpo candidato e profondo 80 mm: piano porta a y=−80. La camera di cottura va da y=0 a y=410; il focolare posteriore da y=410 a y=660, profondo 250 mm, con larghezza da 790 a 510 mm. La luce porta candidata e 720 × 160; la botola posteriore candidata e 300 × 140. Sono quote interne e candidate, non quote di produzione.

La canna candidata ha asse (395, 45), diametro interno 130, collare Ø190 e altezza candidata 1000 oppure 1500. Questi valori restano modificabili e da verificare; in pianta il collare può sovrapporsi alle pizze. Le aree nette aria 60 e 90 cm² sono scenari per la verifica dell'aria di combustione, non fori da costruire. Il gioco radiale indicativo di 1 mm attorno ai dischi e un'ipotesi da verificare in progetto meccanico, non una tolleranza di taglio accettata; non sono quindi fornite quote esecutive dei fori.

Esistono il modello termico V3 e una verifica separata della rete di pressione per la geometria compatta. Questa V4 non e ancora un modello Simulink validato: quando il design avra fissato volta, focolare, collettore e aria, il modello va aggiornato e verificato con quella geometria. I [risultati preliminari](riferimenti/VERIFICHE_COMPATTA.md) e i dati numerici sono conservati nella cartella `riferimenti`; la verifica di captazione a porta aperta resta irrisolta.

Fonti: file locali del progetto e quote concordate nella conversazione del 2026-09-21.
