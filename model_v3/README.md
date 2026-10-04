# Forno V3 — modello parametrico di progetto

Questa versione implementa una prima rete termica dinamica per confrontare geometrie e materiali. È eseguibile in MATLAB e tramite un modello Simulink nativo. È un modello di progetto **non ancora calibrato**: i risultati numerici non costituiscono un dimensionamento definitivo della canna fumaria né una previsione validata della cottura.

## Vincoli confermati

- Piano anteriore interno: **790 × 410 mm**, in cordierite.
- Due inserti rotanti in cordierite, **diametro 320 mm** ciascuno, complanari al piano.
- Fuoco nella zona posteriore, con botola di carico sul retro.
- Forno all'aperto con camino proprio.
- Obiettivo: due pizze napoletane, con osservazioni a 60 e 90 secondi.
- Confronto fra guscio in acciaio isolato e guscio refrattario isolato.

I file originali della bozza restano nella cartella superiore.

## Avvio

In MATLAB, dalla cartella `model_v3`:

```matlab
p = oven_defaults();
r = oven_simulate(p);      % una configurazione
study = run_oven_study();  % verifiche + otto confronti + grafici + rapporto
build_oven_simulink(p);
open_system('oven_model_V3');
```

Il modello Simulink contiene i parametri nel **Model Workspace**, variabile `ovenV3_p`. Il callback di inizializzazione ricalcola la geometria; il bilancio è lo stesso `oven_rhs.m` usato da MATLAB. I due blocchi Step inseriscono ed estraggono entrambe le pizze. Gli Scope mostrano temperature in °C; l'uscita `oven_states` conserva gli stati in unità SI. Il modello utilizza una S-function MATLAB Level 2 e la simulazione normale, senza generazione di codice.

Per cambiare configurazione e rigenerare il modello:

```matlab
p = oven_defaults();
p.geom.rearDepth = 0.24;
p.geom.height = 0.28;
p.geom.rise = 0.11;
p.flow.chimneyDiameter = 0.13;
p.flow.chimneyHeight = 1.0;
p.flow.chimneyPosition = 'front';
p.roof.material = 'refractory';
p.rotation.rpm = [2 2];
r = oven_simulate(p);
build_oven_simulink(p);
```

Questi valori illustrano come usare i parametri: non sono misure consigliate per costruire il forno.

## Geometria

L'origine della pianta è all'angolo anteriore sinistro; `x` attraversa la larghezza e `y` aumenta verso il fuoco. I centri dei dischi sono inizialmente `(210,205)` e `(580,205)` mm. Restano 50 mm fra i bordi dei dischi e le pareti laterali, 50 mm fra i due dischi e 45 mm davanti/dietro. Il gioco radiale provvisorio di 1 mm viene sottratto alla pietra fissa; non è una tolleranza costruttiva verificata.

La ripartizione delle aree è:

`A_fissa + 2 A_disco + A_giochi = 0.790 × 0.410 m²`.

Le masse non includono due volte i dischi. La parte fissa e i dischi usano gli stessi parametri di cordierite. Il focolare ha inizialmente lo stesso materiale e spessore: è una **ipotesi da sostituire** se verrà usato un refrattario diverso.

La zona posteriore è un trapezio con base anteriore 790 mm, base posteriore 510 mm e profondità iniziale 140 mm, ereditata dalla bozza. Il confronto include anche 240 mm. La potenza del fuoco resta uguale nei due casi: il modello non deduce la quantità di legna ammissibile dal volume libero.

`roofShape='barrel'` indica una volta a sezione **parabolica**, non un arco circolare:

`z(x,y) = h_imposta + rise · [1 − (2x/w(y) − 1)²]`.

`height` è la quota massima e `rise` la freccia; `h_imposta = height − rise`. Sul retro la larghezza `w(y)` si restringe linearmente. Aree del tetto, pareti e volumi sono ricavati dalla geometria. L'alternativa `flat` mantiene la quota `height` e annulla la freccia. Dimensioni e volumi sono interni: ingombro esterno, telaio, rivestimento e motori vanno aggiunti.

Il disegno del camino in pianta è una proiezione della presa superiore vicino alla bocca, **non un foro nel piano di cordierite**. La coordinata esatta della presa e la geometria della cappa non sono risolte dalla rete termica.

## Stati e bilanci

Con otto settori per disco sono presenti 90 stati:

- gas nella zona anteriore e in quella posteriore;
- guscio anteriore e posteriore, ciascuno con strato interno ed esterno;
- pietra fissa e focolare, ciascuno con strato superiore ed inferiore;
- due dischi, ciascuno con otto settori e due strati nello spessore;
- due pizze, ciascuna con otto settori: temperatura base, temperatura superiore e acqua residua.

Per ciascun nodo termico si integra `C_i dT_i/dt = somma delle potenze entranti − somma delle potenze uscenti`, con `C_i = rho cp V_i`. I nodi di acqua sono espressi in kg. Temperature in kelvin nel calcolo, gradi Celsius nei grafici.

Gli scambi interni sono aggiunti a un nodo e sottratti all'altro:

- convezione: `Q = h A (T_gas − T_superficie)`;
- conduzione nello spessore fra i due centri: `Q = (2 k A / spessore) (T_1 − T_2)`;
- radiazione efficace: `Q = epsilon_eff sigma A peso (T_guscio^4 − T_superficie^4)`;
- contatto pietra/pizza: `Q = h_contatto A (T_pietra − T_base)`;
- evaporazione: `Q_evap = L_vap · portata_acqua`.

La pizza scherma la corrispondente area del disco. L'irraggiamento ricevuto dalla pizza viene sottratto al guscio; non viene contemporaneamente inviato alla pietra sottostante. Le perdite esterne comprendono isolamento, radiazione dalle aperture e calore portato fuori dal camino.

L'evaporazione è limitata dall'energia netta positiva disponibile in ciascun nodo della pizza. Fra 100 e 102 °C una transizione regolarizzata devia questa potenza verso il calore latente. Finché l'acqua del settore è disponibile, il nodo umido non continua a scaldarsi arbitrariamente sopra questa fascia; all'esaurimento riprende il riscaldamento sensibile. Base e parte superiore condividono l'acqua del settore, senza resistenza interna al trasporto di umidità. La transizione in temperatura e la piccola soglia di acqua residua sono regolarizzazioni numeriche, non parametri identificati dell'impasto.

Il modello della pizza è calorimetrico: capacità costanti e legge di evaporazione semplificata. Non descrive migrazione interna dell'acqua, rigonfiamento, crosta, doratura, condimenti o chimica di cottura. Non si deve interpretare una temperatura media come criterio di pizza pronta.

## Rotazione

Ogni settore ruota con `theta(t) = theta_0 + 2 pi rpm t / 60`. Il peso di esposizione alla zona posteriore varia con l'angolo. I valori medio e di ampiezza sono parametri **ipotizzati**, non ricavati da una simulazione dei fumi. Il test a campo uniforme verifica che cambiare velocità non introduca un beneficio artificiale.

Il modello calcola quindi l'effetto della rotazione **dato un gradiente di esposizione**. Le due posizioni laterali sono simmetriche e non è modellata una disuniformità destra/sinistra. La velocità non modifica il coefficiente convettivo; supporti, alberi, motori, cuscinetti e ponti termici non sono ancora rappresentati.

## Combustione e camino

La potenza è imposta: `Q_fuoco = kg/h / 3600 × PCI × efficienza`. Una frazione va al gas posteriore; la parte radiativa è ripartita fra guscio anteriore, guscio posteriore e focolare con pesi normalizzati. Non si calcolano accensione, umidità della legna, cinetica, limite di ossigeno o cariche discrete.

Il tiraggio disponibile è `DeltaP = max(0, g H (rho_ambiente − rho_fumi))`. La portata usa le resistenze di ingresso e camino:

`m_dot = sqrt(2 DeltaP / [K_camino/(rho_fumi A_camino²) + K_ingresso/(rho_ambiente A_ingresso²)])`.

La perdita è `Q_camino = m_dot cp (T_uscita − T_ambiente)`. I coefficienti globali K devono essere identificati per tubo, raccordi, presa e cappa reali. La temperatura del gas di zona viene usata come temperatura del camino: non sono calcolati il raffreddamento lungo il tubo e il vento.

Con uscita frontale la rete assume un percorso efficace ambiente → retro → fronte → camino, che rappresenta un sottocorrente d'aria verso il fuoco e un ritorno caldo verso la bocca. Con uscita posteriore usa ambiente → fronte → retro → camino. È presente un ricircolo simmetrico parametrico fra le zone. Questo confronto **non determina se la cappa cattura il fumo**, né il rischio di riflusso. Un'apertura della botola è un parametro statico; il gesto di caricare legna e la relativa perturbazione non sono simulati.

## Parametri provvisori più influenti

| Parametro | Riferimento iniziale | Da verificare con |
|---|---:|---|
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

La densità della cordierite resta quella della bozza per tracciabilità; non va considerata un dato identificato. IPS, ad esempio, pubblica densità tipiche differenti per i propri prodotti. Le proprietà a temperatura ambiente non sono automaticamente valide a temperatura di cottura.

## Risultati e verifiche

`run_oven_study` esegue otto casi: riferimento acciaio, refrattario, volta piana, focolare più profondo, camino più largo, camino più alto, camino posteriore e dischi fermi. Ogni caso modifica un parametro del riferimento. Il confronto acciaio/refrattario riguarda il **guscio completo di pareti**, non la sola copertura: questa è una semplificazione esplicita della versione V3.

Tutti i casi hanno uguale potenza del fuoco e iniziano a temperatura ambiente. Il carico dopo 30 minuti è un istante di confronto, non l'affermazione che entrambi i materiali siano già pronti. Un forno più lento va confrontato anche a parità di temperatura iniziale prima di giudicarne la tenuta in cottura.

`results/study.mat` conserva parametri, stati, diagnostiche, indicatori e limiti; `confronto.csv` contiene gli indicatori riassuntivi. `RISULTATI.md`, `geometria.png` e `confronti.png` permettono di leggere il confronto. Il tempo di raggiungimento di 400 °C nel CSV è solo una soglia di osservazione, non un requisito imposto alla pizza napoletana.

`oven_validate` verifica geometria, conservazione dell'energia con entrambi i materiali e posizioni del camino, irraggiamento reciproco e schermatura delle pizze, equilibrio senza fuoco, acqua non negativa, comportamento senza tiraggio, assenza di effetto rotazione in campo uniforme e convergenza numerica. Queste sono verifiche del codice, distinte dalla validazione fisica.

Il residuo istantaneo `storedPower − (fuelPower − lossPower − evapPower)` deve essere prossimo allo zero. Il bilancio integrale calcolato sui campioni salvati ha anche un errore di quadratura: ridurre `outputStep` prima di confrontarlo con una tolleranza stretta. Le pizze estratte rimangono come stati congelati di contabilità energetica e non scambiano più calore con il forno.

## Come arrivare alle misure costruttive

1. Scegliere pietra, refrattario e isolamento reali e aggiornare le proprietà; specificare anche il materiale del focolare.
2. Fissare ingombro, dimensioni dei ciocchi, autonomia e accesso delle due pale; questi vincoli non sono ricavati dalle sole temperature.
3. Confrontare altezza/freccia della volta, profondità del focolare, bocca, isolamento e potenza con intervalli di incertezza sui coefficienti.
4. Ricavare fattori di vista dalla geometria e un campo di esposizione spaziale; verificare cappa e percorso dei fumi con un modello fluidodinamico o prove di flusso.
5. Calibrare con termocoppie su pietra superiore/inferiore, guscio, gas posteriori e camino, misurando consumo di legna e tiraggio; ripetere con due carichi uguali.
6. Solo dopo questi controlli fissare dimensioni definitive e dettagliare dilatazioni, appoggi, giochi, alberi, motori, pulizia e struttura.

## Riferimenti tecnici

- [NIST TN 1958](https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1958.pdf): condizioni di scambio convettivo e radiativo; dipendenza dei fattori di configurazione dalla geometria.
- [NIST: modello di radiazione grigia e diffusa](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=841367): bilanci radiativi tramite fattori di vista e radiosità. La V3 usa pesi efficaci conservativi, non implementa l'intero metodo di radiosità.
- [DOE/OSTI: natural draft, appendice A](https://www.osti.gov/servlets/purl/1219888): differenza di densità, altezza del camino e riduzione del tiraggio per le perdite.
- [ASHRAE, Chimney, Vent, and Fireplace Systems](https://handbook.ashrae.org/Handbooks/S16/SI/s16_ch35/s16_ch35_si.aspx): fattori che concorrono al tiraggio e al dimensionamento del sistema.
- [IPS Ceramics: piastre e ripiani](https://ipsceramics.com/kiln-furniture/kiln-shelves-and-batts/plain-batts-plates-tiles-and-shelves/): proprietà tipiche e loro dipendenza dal prodotto.
- [CoorsTek: silicati](https://www2.coorstek.com/en/materials/silicates/): proprietà indicative della cordierite.
- [COMSOL: modellazione del raffreddamento evaporativo](https://www.comsol.com/blogs/intro-to-modeling-evaporative-cooling): legame fra flusso evaporato e calore latente. La chiusura limitata dall'energia della V3 è un'approssimazione propria; non implementa il trasporto accoppiato di umidità descritto nel riferimento.
- [MathWorks: S-function MATLAB Level 2](https://www.mathworks.com/help/simulink/sfg/writing-level-2-matlab-s-functions.html): adattatore continuo usato nel modello Simulink.
