# C02 — gate componenti e piano del banco

**Piano di sviluppo, non istruzioni di fabbricazione/accensione.** C02 non
autorizza prove a fuoco o produzione. Appoggi, isolamento, elettrico e scarico
devono essere dimensionati e riesaminati da tecnici competenti prima di un
banco caldo; luogo esterno idoneo, protezioni, monitoraggio e arresto definiti.
Non usare il prototipo sotto tettoie o vicino a combustibili senza verifica
specifica dell'installazione. Il prodotto camino non rende sicuro il forno.

## A — configurazione identificata

- Un solo modulo completo prima del forno intero: pietra, ripartitore,
  distanziali, isolante incapsulato, carrier, albero, cartuccia, giunto,
  trasmissione, motoriduttore e schermi, con codici/revisioni e CAD.
- Riferimenti V4 conservati, ma tolleranze ancora aperte; scegliere il gioco
  solo dopo aver misurato diametri, planarità, eccentricità e cicli.
- Riserve del corpo160/50/15 non equivalgono a un pacco componenti verificato.
  Confermare supporto pietra distribuito e percorso carichi indipendente
  dall'isolante. Il distanziale deve avere dati a temperatura, non solo a20 °C.
- Documentare lubrificanti/tenute/avvolgimenti, grado IP, condensa e ambiente.
  24V non rende conformi alimentatore, parti mobili o installazione esterna.

**Gate A:** distinta identificata e CAD montabile; materiali per uso previsto,
criteri termici/carichi/tolleranze scritti e accettati. In mancanza, STOP
alla costruzione del modulo caldo; possibili mockup e prove a freddo protette.

## B — banco a freddo

| Misura | Metodo previsto | Condizione d'uscita |
|---|---|---|
| Catena di carico | Pesatura reale, controllo degli appoggi, verifica flessione/portanza e stabilità | Nessun carico sulla sola lana; pietra/frammenti trattenuti; carichi definiti |
| Momento pala | Caso di progetto con utensile al bordo, dopo dimensionamento | Cartuccia/telaio dimensionati anche a momento;6,4Nm è solo lo scenario40N |
| Coppia | Trasduttore o braccio strumentato, avvio e marcia pulito/sporco | Motore selezionabile dalla coppia misurata più margine motivato, non dal solo0,75–1,35Nm |
| Movimento | Prove a0,3/0,6/1rpm, planarità, eccentricità, oscillazione assiale | Nessun contatto indotto dal difetto misurato; giochi/tolleranze assegnati |
| Detriti | Farina/cenere simulate in banco protetto e pulizia | Nessun ingresso in elettrico/cuscinetti; nessuna fibra nel piano alimentare |
| Manutenzione | Rimozione a freddo di pietra/carrier, sostegno e disaccoppiamento, estrazione frontale | Eseguibile dall'appoggio senza sollevare il forno, spazio servizio dimostrato |
| Guasti | Arresto, blocco controllato, mancanza alimentazione e ripristino | Arresto accessibile, coppia limitata, nessun riavvio inatteso; carter adeguati |

I carichi di prova devono derivare dal dimensionamento:40N e masse C02 sono
ipotesi di screening, NON un collaudo di resistenza già stabilito.

## C — campione termomeccanico, dopo riesame di sicurezza

Proporre sensori calibrati su pietra alto/basso, ripartitore, distanziali,
carrier, albero lato caldo/freddo, anelli/corpo cartuccia, motore, aria vano,
schermo, appoggi e superficie esterna. Includere temperatura e umidità ambiente.
Termografia/IR solo complementari: emissività dell'inox e riflessi possono
rendere la lettura ingannevole. Conservare dati grezzi, calibrazione e incertezza.

Misurare contemporaneamente velocità/coppia/corrente; piano/disco e detriti
all'avvio, a regime e fino al completamento del raffreddamento.
Controllare i massimi **dopo** lo spegnimento o l'arresto della ventilazione.
Rilevare ritiro del pannello, migrazione lana, deformazioni/creep, giunti,
ossidazione, perdite e planarità dopo i cicli. Nessuna brusca bagnatura a caldo.

**Gate C:**

- Ogni componente resta entro il proprio servizio continuo/transitorio
  dichiarato, con margine e incertezza espliciti: niente limite generico per
  «tutti i cuscinetti». Aria vano50 °C rimane un obiettivo modificabile.
- Nessun impuntamento, contatto indesiderato, crepa o perdita di ritenzione;
  nessuna esposizione di fibre; coppia e usura stabili nei cicli scelti.
- Superfici accessibili, protezioni, maniglie e distanze: limiti pertinenti
  definiti prima della prova con il tecnico; questo dossier non inventa un
  unico limite al tatto né trasferisce G50/G75 del camino alla scocca.
- Affidabilità della strumentazione e risposta all'interruzione energia
  dimostrate; i primi cicli non equivalgono a una prova di durata completa.

## D — interfaccia collettore/camino e combustione

1. Definire la geometria tridimensionale vera: fessura, plenum, raccordo,
   collarino, adattatore, supporti, passaggi isolati e accesso pulizia.
   Il collo170×90 è un candidato perØ130, non perØ150.
2. Richiedere CAD piastra/giunti del sistema; distinguere cover260 e base440,
   da integrare sul tetto senza spostare silenziosamente l'asse V4.
3. Modellare/misurare ΔP vs portata: griglia, condotto, distributori,
   braci, collettore, raccordo e terminale. Cd e K non vanno sommati due
   volte per la stessa perdita; la prova di area non basta.
4. Distinguere H idraulica, altezza effettiva del raccordo e innesti955/455;
   pesi, momento del vento, stabilità dell'intero forno e appoggio verificati.
5. Aggiornare CFD con presa vera, materiali coerenti e maglia/calibrazione;
   niente «pronto» da una simulazione che fallisce i criteri di readiness.
6. Captazione: definire con tecnico i limiti pertinenti per ΔP, gas/CO,
   esposizione operatore e distanze, prima delle prove a combustione.
   Rilevare accensione, regime, porte/ricarica, vento e caso avverso;
   la semplice assenza visiva di fumo non è una misura di sicurezza.

La rete1D C02 non prevede combustione, CO, braci o percorso secondario:
lambda totale degli ingressi non garantisce aria effettiva al combustibile.
L'inversione nel caso vento10 indica una configurazione non approvabile
sotto quelle ipotesi, non una previsione della velocità del vento reale.

## E — forno completo e prestazione richiesta

Richiamare il piano C01 senza sostituirlo. Dopo i gate precedenti:
almeno3 partenze da freddo, due pizze simultanee e almeno5 doppie infornate
consecutive; misurare recupero e qualità, confrontando velocità e pietre
10/20/30mm solo con codici reali. Primo obiettivo: pronto entro60min,
miglioramento verso45min; cottura60–90s soltanto quando pronto.

Prontezza termica, distribuzione, superficie esterna, parti mobili e
captazione sono criteri separati: nessuna deroga alla cottura può approvare
un deficit di sicurezza. Allineare le proprietà dei modelli prima di
trasferire risultati fra versioni. Ripetere i casi avversi e i guasti,
poi un piano di durata concordato prima della preserie.

## Rischi da chiudere nel riesame

| Rischio | Misura progettuale/prova richiesta |
|---|---|
| Pietra crepata o disco impuntato | Appoggio distribuito flottante, ritenzione frammenti, giochi e coppia limitata |
| Motore/cuscinetto surriscaldato | Schermatura, ponti termici reali, sonde e picco dopo-spegnimento |
| Farina/cenere nei meccanismi | Labirinto ispezionabile e raccolta distinta; prove pulizia |
| Fumo/CO e inversione | Circuito continuo, captazione e vento misurati; criteri prima della prova |
| Lana/polveri verso cibo | Contenimento e giunti qualificati; procedure produttore per primo ciclo |
| Dilatazioni della camera | Fissaggi indipendenti/scorrevoli, niente scocca bloccata sulla camera |
| Camino instabile | Peso/vento al telaio e appoggio; supporti reali, non claim di catalogo isolato |
| Acqua ed elettrico / riavvio | Installazione protetta, componenti/idoneità outdoor e risposta in guasto |

## Registro minimo di ciascuna prova

Configurazione e revisioni, seriali/materiali, montaggio, strumenti e
incertezza, operatori, condizioni ambiente, carichi/legna e umidità dove
applicabili, tempi, canali grezzi, massimi (anche raffreddamento), esito
per criterio e anomalie. Definire numero/durata dei cicli e soglie prima
di iniziare, senza trasformare valori ipotizzati C02 in limiti certificati.
Applicabilità normativa/MOCA/elettrico e messa sul mercato da stabilire
con il tecnico: C02 non dichiara conformità o autorizzazione alla preserie.
