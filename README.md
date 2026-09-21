# Forno V3 — modello termico parametrico

La V3 è una rete termica dinamica per confrontare configurazioni del forno a due pizze. Rappresenta il piano interno in cordierite da **790 × 410 mm**, due dischi rotanti da **Ø320 mm**, la zona di combustione posteriore, gas, volta, due pizze e il camino. Serve a mettere a confronto geometrie e materiali; è un modello di progetto **non ancora calibrato fisicamente**. I suoi risultati non sono un dimensionamento costruttivo definitivo della canna fumaria, della volta o della cottura.

## Configurazione studiata

- Due pizze napoletane, con istanti di osservazione a 60 e 90 s.
- Forno esterno a legna con camino proprio.
- Due dischi di cordierite complanari al piano fisso, ciascuno con rotazione parametrica.
- Zona di fuoco posteriore con botola di carico.
- Confronto fra guscio in acciaio isolato e guscio refrattario isolato.

Le dimensioni interne, gli spessori, le proprietà dei materiali, la potenza, la bocca e il camino sono parametri provvisori del modello. Non sono quote da costruzione.

## Avvio rapido

Servono MATLAB e Simulink; il modello è stato verificato con R2026a. Aprire MATLAB con questa cartella come cartella corrente e aprire direttamente il modello:

```matlab
open_system('oven_model.slx');
```

I parametri sono già incorporati nel **Model Workspace** del modello; la variabile è `ovenV3_p`. Premere **Run** nella finestra Simulink per simulare.

Per ripristinare i valori di default e rigenerare il modello:

```matlab
run('oven_parameters.m');
% oppure
p = oven_defaults();
build_oven_simulink(p);
```

La rigenerazione sostituisce il file `oven_model.slx`: salvare prima eventuali modifiche manuali al diagramma. Per eseguire gli studi e la verifica dalla cartella radice:

```matlab
p = oven_defaults();
r = oven_simulate(p);
study = run_oven_study();
verify_simulink();
```

Il diagramma usa una S-function MATLAB Level 2 e la simulazione normale, senza generazione di codice. Gli Scope mostrano temperature in °C; `oven_states` conserva gli stati in unità SI.

## Geometria e rappresentazione

L'origine della pianta è nell'angolo anteriore sinistro; `x` attraversa la larghezza e `y` aumenta verso il fuoco. I centri iniziali dei dischi sono `(210,205)` e `(580,205)` mm. La ripartizione delle aree è:

`A_fissa + 2 A_disco + A_giochi = 0.790 × 0.410 m²`.

La zona posteriore è un trapezio: base anteriore 790 mm, base posteriore 510 mm e profondità iniziale 140 mm. Lo studio include anche una variante da 240 mm. La potenza del fuoco è mantenuta uguale nei confronti: il modello non deduce la quantità di legna ammissibile dal volume libero.

`roofShape='barrel'` definisce una volta a sezione parabolica, non un arco circolare:

`z(x,y) = h_imposta + rise · [1 − (2x/w(y) − 1)²]`.

`height` è la quota interna massima, `rise` la freccia e `h_imposta = height − rise`. La variante `flat` annulla la freccia. Quote, volumi e superfici sono interni: struttura, isolamento esterno, rivestimento, motori, alberi, appoggi e giochi meccanici restano da progettare.

La presa del camino disegnata in pianta è soltanto una proiezione vicino alla bocca: non rappresenta un foro nel piano di cordierite. La posizione esatta e la capacità di raccolta della cappa non sono risolte dalla rete termica.

## Stati, scambi e rotazione

Il modello usa 90 stati:

- Gas nelle zone anteriore e posteriore.
- Guscio anteriore e posteriore, con strato interno ed esterno.
- Pietra fissa e focolare, con strato superiore e inferiore.
- Due dischi, ciascuno con otto settori e due strati nello spessore.
- Due pizze, ciascuna con otto settori: base, parte superiore e acqua residua.

Per ogni nodo termico integra `C_i dT_i/dt = ΣQ_entranti − ΣQ_uscenti`, con `C_i = rho cp V_i`. Gli scambi sono convezione, conduzione nello spessore, irraggiamento efficace, contatto pietra-pizza ed evaporazione. Le temperature sono in kelvin nel calcolo e in gradi Celsius nei grafici.

Ogni settore del disco ruota secondo `theta(t) = theta_0 + 2 pi rpm t / 60`. Il modello calcola l'effetto della rotazione **dato** un gradiente di esposizione ipotizzato: non risolve i fumi in 3D, non introduce disuniformità destra/sinistra e non rappresenta motori, cuscinetti o ponti termici.

La pizza è un modello calorimetrico. L'evaporazione è limitata dall'energia netta disponibile, con transizione regolarizzata fra 100 e 102 °C. Non sono descritti migrazione dell'acqua, rigonfiamento, crosta, doratura, condimenti o chimica di cottura; una temperatura media non equivale a pizza pronta.

## Combustione e camino

La potenza del fuoco è imposta:

`Q_fuoco = kg/h / 3600 × PCI × efficienza`.

Non sono calcolati accensione, umidità della legna, cinetica, ossigeno disponibile o cariche discrete. Il tiraggio disponibile è approssimato da:

`DeltaP = max(0, g H (rho_ambiente − rho_fumi))`.

La portata combina resistenze di ingresso e camino; le relative perdite di carico devono essere identificate per presa, cappa, tubo, raccordi e condizioni di vento reali. L'uscita frontale assume un percorso efficace ambiente → retro → fronte → camino. Il confronto non determina la cattura dei fumi dalla cappa, il riflusso o l'effetto dinamico dell'apertura della botola.

## Parametri provvisori più influenti

| Parametro | Riferimento iniziale | Da verificare con |
| --- | ---: | --- |
| Cordierite: densità / cp / conducibilità | 2600 kg/m³ / 900 J/(kg K) / 2.5 W/(m K) | Scheda del prodotto reale alle temperature operative |
| Pietra | 10 mm | Transitorio, resistenza meccanica e shock termico |
| Guscio acciaio | 2 mm | Lega, ossidazione, deformazioni e struttura |
| Guscio refrattario | 30 mm | Tipo di refrattario, massa e conducibilità |
| Isolamento | 50 mm, k=0.055 W/(m K) | Scheda tecnica e dipendenza dalla temperatura |
| Bocca | 600 × 130 mm | Accesso delle pale, perdite e cattura dei fumi |
| Camino | Ø100 mm, altezza 500 mm | Percorso reale, portata, pressione, cappa e condizioni esterne |
| Fuoco | 3.5 kg/h, PCI 15 MJ/kg, efficienza 0.70 | Consumo e combustione misurati |
| Rotazione | 2 giri/min | Uniformità misurata e soluzione meccanica |
| Pizze | Ø300 mm, 250 g ciascuna | Prodotto effettivo; diametro regolabile fino a 320 mm |

## Studi, artefatti e verifica

`run_oven_study` confronta otto casi: riferimento in acciaio, refrattario, volta piana, focolare più profondo, camino più largo, camino più alto, camino posteriore e dischi fermi. Il confronto acciaio/refrattario riguarda il guscio completo di pareti, non la sola copertura.

Gli artefatti della V3 sono nella cartella `results`:

- [Studio e diagnostiche](results/study_V3.mat)
- [Verifica MATLAB–Simulink](results/simulink_validation_V3.mat)
- [Indicatori riassuntivi](results/confronto_V3.csv)
- [Rapporto dei risultati](results/RISULTATI_V3.md)
- [Confronti grafici](results/confronti_V3.png)
- [Geometria parametrica](results/geometria_V3.png)
- [Log di verifica](results/verifica_V3.log)

La verifica del codice controlla geometria, conservazione dell'energia, irraggiamento reciproco e schermatura delle pizze, equilibrio senza fuoco, acqua non negativa, assenza di tiraggio, assenza di effetto artificiale della rotazione in campo uniforme e convergenza numerica. Il residuo istantaneo `storedPower − (fuelPower − lossPower − evapPower)` deve restare vicino a zero. Questi controlli sono **validazione numerica del modello**, non calibrazione fisica del forno.

La verifica della V3 nei percorsi del repository ha superato tutti i 13 controlli numerici. Il confronto dello stesso ciclo in MATLAB e Simulink ha restituito uno scarto massimo di 0,071803 K e nessuna differenza nella massa d'acqua. Sono stati controllati anche apertura del modello, rigenerazione dai parametri predefiniti e nomi dei risultati. I dati degli otto confronti sono quelli dello studio V3 originale; grafici e rapporto sono stati rigenerati da questi dati senza ripetere le otto simulazioni.

## Limiti e prossima calibrazione fisica

Per arrivare a quote costruttive occorre fissare materiali reali, isolamento, ingombro, ciocchi, accesso delle pale e autonomia; poi confrontare volta, focolare, bocca, cappa e camino con prove di flusso o CFD. La calibrazione richiede termocoppie su pietra superiore e inferiore, guscio, gas posteriori e camino, più consumo della legna e tiraggio, ripetuti con due carichi uguali.

Solo dopo si possono definire canna fumaria, dilatazioni, appoggi, giochi, alberi, motori, pulizia e struttura. Il successivo **V4 / dimensionamento** affronta le quote geometriche e il percorso fumi: non fa parte dello snapshot termico V3.

## Riferimenti tecnici

- [NIST TN 1958](https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1958.pdf): scambio convettivo e radiativo e dipendenza dei fattori di vista dalla geometria.
- [NIST: radiazione grigia e diffusa](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=841367): bilanci radiativi tramite fattori di vista e radiosità; la V3 usa pesi efficaci conservativi.
- [DOE/OSTI: natural draft, appendice A](https://www.osti.gov/servlets/purl/1219888): differenza di densità, altezza del camino e perdite.
- [ASHRAE, Chimney, Vent, and Fireplace Systems](https://handbook.ashrae.org/Handbooks/S16/SI/s16_ch35/s16_ch35_si.aspx): fattori che incidono sul tiraggio e sul dimensionamento.
- [IPS Ceramics](https://ipsceramics.com/kiln-furniture/kiln-shelves-and-batts/plain-batts-plates-tiles-and-shelves/) e [CoorsTek](https://www2.coorstek.com/en/materials/silicates/): proprietà indicative della cordierite, da sostituire con quelle del prodotto scelto.
- [COMSOL: evaporative cooling](https://www.comsol.com/blogs/intro-to-modeling-evaporative-cooling): relazione fra flusso evaporato e calore latente; la chiusura V3 resta semplificata.
- [MathWorks: S-function MATLAB Level 2](https://www.mathworks.com/help/simulink/sfg/writing-level-2-matlab-s-functions.html): adattatore continuo del modello Simulink.

## Cronologia Git

Ogni snapshot è un commit separato; non si usano copie ZIP. I percorsi principali restano stabili (`oven_model.slx`, `oven_parameters.m`), mentre report e immagini portano il numero di versione nel nome.

| Versione | Commit / stato |
| --- | --- |
| V0 | `35cda97` |
| V1 | `fe674e3` |
| V2 | `9382afa` |
| V3 | Versione corrente |
