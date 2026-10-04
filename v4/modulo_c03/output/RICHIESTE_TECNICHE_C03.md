# C03 — richieste tecniche da revisionare, NON inviate

Destinazione: un futuro modulo rotante per forno outdoor, uso alimentare;
motore/cuscinetti fuori dalla camera calda, ma temperature effettive non
ancora misurate. Prima valutazione su banco a freddo, poi riesame separato
per calore, umidità, detriti e sicurezza. Nessun ordine o impegno commerciale.

## Motore PG5 / controllo STEPPERONLINE

- Confermare codice17HS19-1684S-PG5, revisione attuale di TDS/curva/STEP: la TDS indica3Nm, curva2Nm; qual è il limite continuo e con quali condizioni?
- Chiarire curva dinamica all'uscita a0,6/1,2/2rpm, avvio e moto continuo al bus24V, corrente limite1,68A/fase e driver/versione consigliati. Non usare coppia di mantenimento come coppia disponibile.
- Chiarire corrente RMS/picco e impostazione conservativa DM542T V4: corrispondenza2,37A peak/1,69A RMS leggermente sopra1,68 nominale. Derating, dissipazione e riduzione a riposo vanno documentati.
- Confermare50N assiali/100N radiali: a quale sbalzo, distanza dal fronte, direzione, vita e temperatura? Pignone con ramo cinghia ancora da dimensionare; nessun carico di pietra/pala applicato al motore.
- Confermare ambiente max50°C, continuità, temperatura corpo/avvolgimenti/riduttore, lubrificante, umidità e IP40; non si presume idoneità outdoor o resistenza a cenere/condensa.
- Fornire CAD attuale con bossØ22,4-M3 profondità4,5, alberoØ8/flat, tolleranze, uscita cavi, raggio curvatura e posizionamento. STEP pubblico importato ma non prova di tolleranze del lotto.
- Proporre feedback di rotazione/impuntamento e limiti per guasto; ALM del driver non misura perdita passi. Arresto e carter restano responsabilità dell'integrazione.

## Alternativa WGA DC

- Confermare WGA-4058247000-G422: TDS04/01/2024 con12rpm/30kgf·cm e pagina/slug8rpm/22kg·cm discordanti. Richiedere rev attuale, curve corrente/coppia/velocità e CAD dello stesso prodotto.
- Quale rapporto o controllo con feedback per0,3–1rpm del disco e coppia misurata futura? Servizio continuo, IP, temperatura ambiente/corpo, carichi albero, EMC e guasto bloccato non documentati nella TDS acquisita.

## Cuscinetti / cartuccia / lubrificazione

- SKF7201 BEGAP: confermare disponibilità/revisione, temperature del cage non-metallico e limiti del prodotto specifico, non della sola famiglia.
- Proposta DB con due unità universali; centri25, punti pressione43 teorici. Chiedere revisione di sedi, spallamenti, raggi, distanziali uguali/rettificati, precarico e serraggio a caldo/freddo.
- Carico scenario assiale110,5N, momento6,4Nm più cinghia: sono ipotesi di dimensionamento, non una prova approvata. Verificare combinazioni, carichi equivalenti/minimi, vita e contaminazione; nessun fattore di sicurezza derivato solo daC0.
- Proporre grasso/tenute compatibili con temperatura, velocità lentissima, intervalli e rischio contaminazione alimentare. Scheda SKF indica senza grasso e senza tenute.
- La cartuccia proposta non è commerciale: richiedere eventuale cartuccia pronta con capacità a momento, CAD e dati termici.

## Pulegge / cinghia MAEDLER

- Codici16221600 (16T),16223200 (32T),16261300 (10T5/280): confermare CAD e dimensioni attuali, fori finiti/calette/calettamenti, tolleranze, flangia/mozzo ed eccentricità.
- Interasse geometrico78,97 e asola ipotizzata75–85 non sono prescrizioni di pretensione. Dimensionare da misure di coppia future, cicli,0,3–1rpm, ambiente e sporco.
- Coppia screening1,346Nm condotta, ramoΔF≈52,84N, avvolgimento16T≈161,44°: tensionamento/denti efficaci/fatica da calcolare. Limite PG5 radiale100N a sbalzo da chiarire; F0=40N solo confronto numerico.
- PuleggiaL21, albero20±1, flat15±0,5: verificare lunghezza utile del vero mozzo e bloccaggio. Boccole/ritenzioni non definite; non proporre un foroØ8 oØ12 senza tolleranze approvate.
- Confermare temperatura cinghia−10/+80°C, derating continuo, umidità, pulizia e materiali per la zona confinata prevista; questo limite non dimostra che il vano resti freddo.

## Promat / pannello sotto piano

- PROMASIL-1000L nominale50: richiedere TDS/SDS Italia attuali; scheda IT archiviata2018-04, SDS acquisita US non trasferibile automaticamente.
- Confermare λ a temperatura media, cp(T), tolleranze, ritiro/cicli, picchi, umidità e contenimento. Nessuna funzione strutturale attribuita al pannello.
- Validare incapsulamento e attraversamenti senza fibre/polveri esposte ad alimenti o fumi. Supporti portanti ceramici separati richiedono codice e dati di creep/resistenza a temperatura.

## Uscita richiesta

Risposta scritta con codici/revisioni, servizio ammesso, limiti e relative
condizioni, CAD dello stesso prodotto, raccomandazioni di montaggio e
condizioni non coperte. Ogni risposta va riesaminata nel dossier; nessuna
risposta di un singolo fornitore approva l'intero forno.
