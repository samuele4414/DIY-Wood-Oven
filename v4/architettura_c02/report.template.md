# C02 — architettura meccanica, materiali e aria–fumi

**Proposta preliminare, non esecutiva.** Si mantengono piano 790 × 410,
dischi Ø320 e centri V4 (210;205)/(580;205), focolare posteriore e scarico
anteriore. Nessun file V4/C01, MATLAB o CFD preesistente viene modificato.
Sono stati eseguiti nuovi calcoli di screening, NON una nuova CFD o prove fisiche.

## 1. Configurazione da portare alla scelta componenti

| Sottosistema | Proposta C02 | Motivo / condizione |
|---|---|---|
| Dischi | Due azionamenti indipendenti, rimovibili | Un blocco non trascina necessariamente l'altro; comando separato |
| Pietre | Appoggio distribuito flottante, senza incollaggio o serraggio rigido all'acciaio | Dilatazioni e fragilità; eventuali frammenti devono restare trattenuti |
| Carrier | Isolante incapsulato; distanziali portanti qualificati; riserva telaio 15 mm | Non attribuire portanza alla lana o a un pannello senza dati |
| Cuscinetti | Cartuccia portante sul telaio inferiore, separata dal riduttore | Peso, pala e disallineamenti non affidati all'albero del motore |
| Motori | Motoriduttori laterali 24 V, trasmissione in vano schermato | Meno altezza che una catena di componenti coassiali |
| Vano | 160 mm netti per il primo prototipo; 120 da recuperare solo con CAD di componenti reali | Margine per giunti, fissaggi, cablaggi e calore |
| Manutenzione | Due moduli estraibili anteriormente, dopo disaccoppiamento a freddo | Appoggio fisso: 25 mm di piedini NON permettono estrazione dal basso |
| Aria | Presa dedicata posteriore, condotto chiuso separato dalla meccanica | Non usare la bocca o il vano motori come unico percorso aria |
| Captazione | Fessura alta + collettore rialzato + raccordo continuo al camino | Il solo foro sul tetto non ha superato il precedente screening a porta aperta |
| Camino | Sistema coibentato dichiarato per il servizio; Ø130 come confronto iniziale | Classificazione, raccordi e sostegni da verificare sul prodotto reale |

La trasmissione a cinghia dentata è candidata SOLO nel vano qualificato freddo.
Se la temperatura non lo consente, confrontare trasmissione metallica o
delocalizzazione dei motori: non chiamare un vano «freddo» solo perché è isolato.
Alimentatore di sicurezza e controllo in posizione protetta dall'acqua e dal calore;
nessun cablaggio esecutivo viene definito qui.

## 2. Catena di carico e termica dei dischi

Pietra → ripartitore caldo con appoggio ampio → distanziali strutturali
termicamente qualificati → carrier irrigidito → albero → cartuccia portante →
telaio. Il pannello isolante riempie il volume ma non è assunto portante.
Il ripartitore deve permettere scorrimento/dilatazione senza concentrare
tre carichi puntuali sulla pietra. Vanno verificati flessione, planarità a caldo,
sbalzo al bordo, tenuta ai frammenti e giochi. I tre appoggi sono un principio,
non un dimensionamento approvato.

Il gruppo pietra/carrier ruota; la schermatura del vano e la protezione contro
farina/cenere restano fisse. Gli attraversamenti richiedono un labirinto
ispezionabile e un elemento raccoglibriciole: NON un'apertura libera ai motori,
NON una guarnizione che striscia sul disco senza averne misurato attrito e calore.
Un giunto deve trasmettere coppia senza irrigidire termicamente il piano.

- Pietra singola 20 mm: **@@STONE_MASS@@ kg**, con densità ancora ipotizzata.
- Assieme con extra 2,5 kg e pizza 0,5 kg: **@@MOVING_MASS@@ kg**.
- Carico assiale di screening con 40 N di spinta pala: **@@AXIAL_LOAD@@ N**.
- La stessa spinta al bordo Ø320 genera **@@TOOL_MOMENT@@ Nm** di momento
  ribaltante: verificare cartuccia e telaio anche a momento, non solo a peso.
- Con `M = mu · F · r + M_tenuta`, r=15 mm, tenuta 0,2 Nm,
  mu=0,03/0,08/0,15: avvio di screening circa **@@TORQUE_MIN@@–@@TORQUE_MAX@@ Nm**,
  incluso moltiplicatore ipotizzato 3. NON è la coppia del cuscinetto reale:
  non risolve attrito di cenere, impuntamento, componenti o guarnizioni scelte.
- Intervallo candidato 0,3/0,6/1 rpm: in 90 s, 0,45/0,9/1,5 giri.
  La rotazione non prova cottura uniforme: confrontare le tre velocità.

Prima di acquistare motori: misurare coppia a freddo/a caldo e attrito sporco;
richiedere coppia continua e spunto dopo riduzione, uso continuo e range termico.
Arresto accessibile, limitazione coppia/corrente e nessun riavvio automatico
dopo mancanza corrente o blocco. Carter contro accesso alle trasmissioni:
la bassa velocità non elimina il rischio di pizzicamento.

### Dilatazioni: perché niente pietra serrata nella lamiera

310S: alpha MEDIO 20–600 °C = 18,8e-6/K dalla scheda Outokumpu, tabella 14.
Ripartitore Ø310 a 600 °C: crescita diametrale **@@STEEL_GROWTH@@ mm**.
Pietra Ø320 a 450 °C con alpha ASSUNTO 3e-6/K: **@@STONE_GROWTH@@ mm**.
La differenza di deformazione equivalente su 320 mm è **@@STRAIN_DIFF@@ mm**.
Le temperature sono scenari, non previsioni e non sono uguali per tutte le parti.

**Questo NON dimostra che il gioco radiale V4 di 1 mm sia insufficiente.**
Quel gioco è tra disco e piano fisso, non tra pietra e ripartitore d'acciaio:
dipende da materiali dei due bordi, transitori termici, eccentricità,
oscillazione assiale e sporco. Confrontare 1/2/3 mm su banco protetto;
non emettere profili di taglio prima della prova. I ponti nominali tra i fori
sono 48/46/44 mm, quelli anteriori 44/43/42 mm: nessuna verifica a flessione.
Piano fisso preferibilmente modulare e appoggiato al proprio telaio,
non una lastra fragile sostenuta attraverso i soli ponti stretti.

### Ponte termico dell'albero

Esempio monodimensionale `Q=k A ΔT/L`, k=20 W/(m K), L=80 mm, ΔT=300 K:
Ø12 pieno **@@SHAFT_SOLID@@ W**, Ø12/8 cavo **@@SHAFT_HOLLOW@@ W**, Ø18 pieno
**@@SHAFT_LARGE@@ W**, PER albero. È un confronto di conduzione, non la
temperatura del cuscinetto. Esclusi irraggiamento, contatti, altri appoggi,
guarnizioni e transitorio. Un albero cavo non è automaticamente resistente.
Verificare dopo-spegnimento: il picco nella meccanica può arrivare più tardi.

## 3. Ingombri: evoluzione della C01, non sostituzione silenziosa

Per modulo si riservano 240 × 180 in pianta. I due rettangoli rimangono
sotto il piano nominale, separati da **@@MODULE_GAP@@ mm**; non verificano
fissaggi, tensionamento, cablaggio o percorso di estrazione completo.

| Architettura riservata | Altezza richiesta | Residuo vano 120 | Residuo vano 160 |
|---|---:|---:|---:|
| Motore laterale: 12 + 25 + max(45;70) + 10 | @@PARALLEL_HEIGHT@@ | @@PARALLEL_120@@ | @@PARALLEL_160@@ |
| Coassiale: 12 + 45 + 20 + 70 + 10 | @@COAXIAL_HEIGHT@@ | @@COAXIAL_120@@ | @@COAXIAL_160@@ |

Tutte le altezze sono riserve, NON dimensioni di modelli commerciali già scelti.
Tre millimetri residui non sono un margine convincente di montaggio/manutenzione.
Proposta: laterale + 160 netti. Carrier da 1,5 a 15 mm di altezza riservata,
vano da 120 a 160: incremento stimato **@@BODY_INCREMENT@@ mm** rispetto C01.

Mantenendo le altre ipotesi, corpo con piedini circa **@@BODY_WIDTH@@ ×
@@BODY_DEPTH@@ × @@BODY_HEIGHT@@ mm**, collare, camino e raccordi esclusi. Il nuovo
collettore/collare NON è un assieme CAD integrato già verificato: questa altezza
è il budget del corpo, non un ingombro totale definitivo.
Riservare 300 mm di spazio servizio frontale. A freddo: togliere pietra e
carrier rimovibili, sostenere il gruppo, disaccoppiare, quindi estrarre la
cartuccia dal fronte senza sollevare tutto il forno. Occorre dimostrarlo
su CAD e montaggio a freddo, non eseguirlo su un forno caldo.

## 4. Aria dedicata: aree libere e perdite distinte

Presa posteriore regolabile e anti-pioggia → condotto chiuso → distributori
laterali del focolare. Evitare interferenza con botola posteriore e supporti
della pietra. Risalita ed uscite laterali sono ancora uno schema funzionale,
non coordinate di foratura. La meccanica ha ventilazione separata.
Niente collegamento aperto tra focolare, briciole e vano elettrico.

Confrontare **60/90/120 cm² NETTI**. Se una griglia fosse libera al 60%,
servirebbero 100/150/200 cm² LORDI, poi si aggiungono le perdite della griglia.
Esempio 300 × 50 mm = 150 cm² lordi, non 150 netti con quella griglia.
Con 90 netti, una prima ripartizione di AREA 60 primaria + 30 secondaria è
solo una variabile di prova: **non garantisce la stessa ripartizione di portata**.
Braci e condotti in parallelo vanno modellati/misurati separatamente.

La presa può essere regolata ma non approviamo posizioni «chiuso» durante
combustione: flusso minimo e comportamento in guasto sono da verificare.
Nessuna serranda aggiunta può interrompere lo scarico fumi; il regolatore
eventuale del camino va concordato con un tecnico, non dedotto dal render.

### Nuova rete di pressione, senza CFD

Porting trasparente della rete MATLAB precedente: stessa densità ideale,
apertura bidirezionale, conservazione massa inclusa legna gasificata,
con nuove sensitività di perdita della presa. Riprodotti il caso base
lambda≈1,87, margine≈−0,97 Pa e uscita bocca aperta≈60,8 kg/h.

Legna IMPOSTA 4,5 kg/h, umidità 20%, gas camera IMPOSTI 500 °C, media canna
250 °C, ambiente 25 °C; Cd=0,65, Darcy=0,03 e K fumi=4. Per lambda=2:
aria **@@REQUIRED_AIR@@ kg/h**, **@@AIR_VOLUME@@ m³/h** all'ambiente.
La potenza CFD 18,75 kW non è trasferita a questa rete e nessuna combustione
reale dei ciocchi viene simulata. I parametri non sono una carica operativa.

| Caso | Lambda dalla presa | Gas uscenti dalla bocca kg/h | Margine chiusa a lambda=2 Pa |
|---|---:|---:|---:|
@@PRESSURE_TABLE@@

Punto di confronto C02: presa 90 netti, Ø130, H1,5, K aggiuntivo presa=2:
margine **@@PREFERRED_MARGIN@@ Pa** nelle sole ipotesi favorevoli.
Con T150 °C/Kfumi8/pressione avversa del vento 3 Pa diventa **@@ADVERSE_MARGIN@@ Pa**. Il deficit mostra
che 90 cm² non è una dimensione universalmente adeguata.
Con porta aperta la rete continua a prevedere **@@OPEN_OUTFLOW@@ kg/h di GAS**
uscenti: non massa di fumo/CO e non una prova sul nuovo collettore tridimensionale.

**H della rete è dal colmo caldo z280 al terminale**, come nel modello MATLAB;
H1,5 non significa 1,5 m di moduli commerciali sopra il collare. L'aumento
di quota e le perdite del raccordo sono da risolvere nella futura geometria.
Non attribuiamo un guadagno di tiraggio gratuito al collare rialzato.
I casi a temperature imposte non risolvono il bilancio energetico; una
temperatura assegnata può non essere sostenibile nel forno reale.

## 5. Captazione e collo: il volume C01 non è un condotto

Proposta per Ø130: ingresso LIBERO 640 × 30 = **@@ENTRY_AREA@@ cm²**;
collo LIBERO 170 × 90 = **@@NECK_AREA@@ cm²**; tubo Ø130 = **@@PIPE_AREA@@ cm²**.
La fessura con pelli 1,5 ha inviluppo 643 × 33 e sta nella riserva C01
650 × 35 SOLO all'ingresso. Il collo alto non ci sta: deve risalire,
attraversare la volta con un adattatore e raccordarsi in modo graduale.

Restringendo direttamente da 640 a 130 mantenendo h30, il passaggio sarebbe
39 cm², solo **@@FLAT_NECK_PERCENT@@%** dell'area del tubo.
Con larghezza 130 servono almeno 102 mm di altezza per eguagliare l'area,
senza che ciò garantisca basse perdite. Il collo 170 × 90 NON è adeguato
al confronto Ø150 secondo il criterio prudenziale di area ≥ tubo:
153 < 176,7 cm². La variante Ø150 richiede un collettore proprio.

Nessun criterio di area dimostra captazione: servono forma reale, perdite,
stratificazione e prova apertura frontale/ricarica posteriore. Tenere una
spalla/raccolta superiore che non scenda nella luce candidata 720 × 160;
dimensionare i labbri e il raccordo prima della nuova CFD. Prevedere pulizia
del collettore e tenuta dopo dilatazione senza scaricare peso sulla volta.

## 6. Collare e camino reale: correzione importante della C01

Il collare C01 ha in cima ottagono circoscritto Ø152, circa **@@OLD_COLLAR@@ mm
tra facce** prima di sottrarre la pelle. Non contiene un camino coibentato.
Il catalogo italiano SUPER ICS riporta per DN130/25 diametro esterno 180,
non 132 del tubo monoparete illustrativo della C01.

Riservare inizialmente **260 mm tra facce nella parte superiore**; il budget
illustrativo DN130, pelli 1/1, isolamento locale 50 e margine 10 per lato chiede
256 mm includendo anche la cover da 1 mm. Non sono dimensioni del prodotto
Schiedel da 50, ancora da chiedere. Per DN150/50 lo stesso budget chiede 276:
la riserva 260 non basta. La quota 260 è tra facce ESTERNE della cover.

**Non basta il diametro:** la piastra di supporto DN130/25 del catalogo è
A238/B306 mm. Con 10 per lato e cover 1, il rettangolo di budget è 260 × 328.
Un ottagono regolare non lo contiene solo perché supera 328: anche i vertici
del rettangolo devono passare le facce a 45°. Si assumono normali delle facce
lungo X/Y e a 45°, non l'orientamento del collare originale C01. Occorrono almeno
**@@PLATE_OCTAGON_MIN@@ mm tra facce esterne** nel budget prudenziale.
**La prima idea di base 340 viene quindi scartata per l'ottagono regolare.**
Riserva di confronto 440, oppure base sfaccettata asimmetrica da disegnare.
Con asse V4 (395;45), una base 440 tra facce sporge in pianta di
**@@COLLAR_OVERHANG@@ mm** davanti alla pelle C01: raccordo e scocca vanno
ridisegnati prima di dichiarare l'ingombro completo. Le quote A/B sono
trattate come inviluppo rettangolare prudenziale; CAD effettivo da richiedere.
Il collare superiore 260 NON verifica piastra o interfaccia strutturale.
Il peso del tubo DN130/25 è 7,68 kg/m: 1,5 m valgono 11,52 kg prima di
terminali e raccordi. Peso e vento vanno al telaio, non alla scocca da 1 mm
o alla volta da 1,5. Non sovrainterpretare il claim «3 m senza tiranti»:
presuppone supporti del sistema, non valida questo forno.

Nel catalogo, H1000 ha h utile 955 e H500 h utile 455: la somma utile 1410
non è 1500. Raccordi, innesti, terminale e la definizione dell'altezza idraulica
vanno quotati. Verificare DoP attuale, combustibile, regime a secco,
temperatura (T450/T600), fuliggine e distanze a combustibili pertinenti.
Le distanze G50/G75/G25 del catalogo non sono temperature sicure al tatto.
Non trasferire la certificazione del camino al forno o al collare personalizzato.

## 7. Materiali: shortlist documentata, non acquisti

@@MATERIAL_TABLE@@

WM970: lambda(T) varia molto; a 400 °C è 0,096, a 600 °C 0,157 W/(m K).
Non sostituire questi dati con una lambda edilizia costante a temperatura
ambiente. Servizio 680 °C non implica legante inalterato, portanza o
compatibilità alimentare. Le fibre restano incapsulate, con giunti e
primo riscaldamento qualificati; la faccia calda deve restare entro il
servizio reale dichiarato con margine motivato. Dove non è possibile,
non si approva il sandwich previsto: occorre rivederlo con il fornitore.

Nessuna temperatura esterna o prontezza 45–60 min è calcolata in C02.
La campagna precedente da 3600 s resta non pronta e con materiali diversi.

## 8. Uscita della fase e gate successivo

**Architettura proposta:** laterale 160, carrier flottante, aria separata,
collettore rialzato, camino coibentato e collare da ingrandire.
**Restano aperti:** codici reali per pietre/supporti/motori/cuscinetti/isolanti,
raccordo integrato, tolleranze, temperatura vano, captazione e conformità.

1. Compilare `RICHIESTE_FORNITORI.md` e ricevere CAD + schede di almeno una
   configurazione completa; nessun contatto o ordine è stato fatto da questo studio.
2. Integrare i componenti nel CAD e dimostrare estrazione frontale, montaggio,
   accesso pala e carichi del camino; prima lavorare a freddo su un modulo disco.
3. Campione carrier/sandwich: coppia e temperature reali; isolamento dei
   frammenti/fibre, appoggi e giochi dopo cicli controllati.
4. Nuova CFD del circuito aria–collettore quotato, con perdite/materiali reali,
   maglia e calibrazione: non avviare una campagna completa su riserve vuote.
5. Prototipo strumentato: avvio, ricarica, vento, porta aperta/chiusa, due pizze,
   cinque doppie consecutive e recupero; poi screening di durata e preserie.

## Provenienza e riproducibilità

@@TEST_COUNT@@ test numerici superati; massimo residuo di massa nella rete
**@@MASS_RESIDUAL@@ kg/s**. È validazione del calcolo, non del forno.
`assunzioni.json` distingue proprietà documentate da ipotesi;
`materiali_candidati.json` contiene fonti, date e curve da trasferire ai modelli.
`output/calcoli_C02.json`/CSV includono tutte le sensitività;
`output/distinta_preliminare.csv` elenca gruppi e quantità di studio, senza
codici ordinabili o metrature congelate. `output/materiali_C02.json` esporta
la shortlist e le curve documentate (archivi nella cartella C02, un livello sopra).
`output/provenienza.json` registra hash delle fonti e dei file preesistenti letti.
Le tavole sono schemi/riserve, non profili esecutivi, e non sostituiscono C01.

@@SOURCES@@
