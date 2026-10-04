# C03 — componenti reali e integrazione digitale del modulo a freddo

03/10/2026. **Studio non esecutivo, non distinta acquisti, non approvato per produzione.**
Nessuna prova fisica, accensione, nuova CFD, richiesta inviata o acquisto.
C01/C02 e geometria V4 restano separati e immutati.

## Esito della fase

- Acquisite18 fonti pubbliche, fra cui schede e STEP di due motoriduttori.
- Importazione OCC riuscita: PG5 un solido, WGA10 solidi; non validazione di revisione o tolleranze del prodotto.
- STEP C03 misto con21 solidi: **un motore reale da STEP e20 inviluppi di studio**. Rilettura STEP coerente; nessuna sovrapposizione oltre soglia numerica0,001mm³ nei@@BOOLEAN_COUNT@@ confronti booleani dopo filtro degli ingombri. Non sono verificati tutti i componenti di un modulo reale.
- Proposta di banco: PG5 passo-passo + cinghia T5 16/32, cartuccia separata con due7201 BEGAP candidati, driver esterno.
- Inviluppo freddo240 × 180 × @@HEIGHT@@ nel vano160: residuo inferiore@@BOTTOM@@ grezzo, @@AFTER_RESERVE@@ oltre riserva10. Il precedente117 di C02 era una somma di riserve diverse, non l'altezza di questo modulo.
- Manutenzione proposta mediante abbassamento12 ed estrazione frontale: passaggio280 × 144 **ancora stretto**, con@@PORT_TOP@@ /@@PORT_BOTTOM@@ residui verticali dopo margini3. Non congelare porta di servizio e quote.

Il corpo resta nel budget C02 circa965 × 915 × 671, esclusi collare/camino:
non è stato rigenerato come assieme completo. Isolamento75, pannello50 e
carrier15 restano ipotesi. Nessuna conferma dei45–60min o dei60–90s di cottura.

## Scelta dei candidati e discrepanze documentali

@@COMPONENT_TABLE@@

Quantità della tabella riferite a un modulo di studio; P02 è un'alternativa,
non un terzo motore. Per due moduli il driver è uno per asse, ma alimentatore,
controller, cavi, protezioni, sensori, quadro e minuteria non sono selezionati.
La distinta CSV è incompleta e non abilita ordinazioni. Appoggi caldi,
pietre alimentari e grasso non hanno ancora codici qualificati.

### Motore e controllo

Il PG5 è **un cambio di candidato rispetto ai motori DC24V generici C02**:
le fasi del passo-passo non vanno alimentate direttamente a24V. La curva
acquisita usa DM542T,24V,2000 impulsi/giro motore e1,69A; non dimostra coppia
al regime del forno. TDS:3Nm massimi; curva:2Nm massimi. La coppia di
mantenimento0,52Nm senza riduttore non è coppia dinamica disponibile.

Riduttore57/11, cinghia2:1, rapporto totale@@RATIO@@. Range disco0,3–1rpm:
riduttore0,6–2rpm; motore3,11–10,36rpm. I microstep migliorano la regolarità
ma non garantiscono precisione o coppia proporzionale al loro numero.
La perdita passi non è rilevata dal driver open-loop. Arresto e rilevazione
di impuntamento richiedono un progetto indipendente; ALM non basta.

@@SPEED_TABLE@@

La voce2,37A picco /1,69A RMS del driver è solo una corrispondenza documentale:
**1,69 supera leggermente gli1,68A/fase del motore** e non è qui approvata
come impostazione. Corrente effettiva, limite conservativo e revisione
devono essere concordati e misurati. La rete230V/alimentatore resta affidata
a tecnico competente. Bus24V non elimina rischi di corto, schiacciamento,
acqua o riavvio inatteso.

Per WGA la scheda04/01/2024 indica12rpm nominali e30kgf·cm (2,94Nm),
16rpm a vuoto. Lo slug commerciale conserva8rpm/22kg·cm: non viene usato
come dato. Con16/32 resterebbero6rpm nominali sul disco; per0,3–1 serve
altra riduzione o un controllo qualificato, non solo una promessa PWM.

## Geometria e carichi: formule e limiti

### Cinghia

Raggi primitivi r=z·p/(2π):@@RS@@ e@@RL@@. Per un anello inestensibile aperto:
L=2√(C²−Δr²)+π(r1+r2)+2Δr·asin(Δr/C).
ConL280 risultaC=@@CENTRE@@; non un interasse di montaggio/tensionamento.
Avvolgimento pignone@@WRAP@@°, circa@@TEETH@@ denti geometricamente coinvolti.
Asola di confronto75–85: capacità denti, minimo denti efficaci, rigidità,
prestiramento, allineamento e fatica devono essere verificati dal fornitore.

Scenario di coppia ereditato da C02: avvio fino a@@TORQUE@@Nm sul disco,
senza impuntamenti reali. Con efficienza cinghia ASSUNTA0,9 la richiesta
all'uscita PG5 è@@MOTOR_TORQUE@@Nm. Non equivale a motore qualificato.
ΔF=T/r_condotta=@@DELTA_FORCE@@N. Nel modello elastico simmetrico semplificato:
F_tesa=F0+ΔF/2, F_lenta=F0−ΔF/2; F_rad=√[(2F0cosθ)²+(ΔFsinθ)²].
Valori negativi del ramo lento invalidano questa ipotesi, non sono forze reali.

@@BELT_TABLE@@

F0=40 è solo il punto di confronto, **non un precarico prescritto**.
F_rad≈@@RADIAL@@ contro limite albero100N, ma distanza di applicazione,
cicli e interazione assiale non sono chiariti nella TDS. A60N per ramo
il limite è già superato nello scenario. Il tensionamento reale può
richiedere un supporto indipendente del pignone e un layout diverso.

### Portanza e cartuccia

Pietra20 ipotizzata@@STONE_MASS@@kg, massa rotante con pizza@@MOVING_MASS@@kg;
con40N di utensile si ottengono@@AXIAL@@N assiali e6,4Nm al bordo.
Il PG5 ammette50N assiali: **vietato dedurre che possa portare il disco**.
Catena proposta: appoggio distribuito qualificato → albero/cartridge →
supporti rigidi → telaio → appoggio. Non scaricare su lana, PROMASIL o scocca.

Cuscinetti d12/D32/B10, angolo40°, C7,61kN/C0=3,8kN: sono dati di catalogo,
non resistenza del modulo. Due cuscinetti universal matching non sono
una coppia già montata/precaricata. Ipotesi a O (DB): centri a−141/−166,
separazione25; a14 è dal fianco e non dal centro, quindi punti di pressione
a−132/−175, distanza43. Richiede orientamento corretto e sedi/distanziali reali.

Momento6,4/0,043 dà@@COUPLE@@N per reazione radiale di coppia.
Forza cinghia applicata20,5 sopra il punto superiore; sovrapposizione
conservativa nella direzione peggiore: superiore@@UPPER_REACTION@@N,
inferiore@@LOWER_REACTION@@N. Non includono precarico, ripartizione assiale,
urti, guasti o rigidezza; **non sono P/P0 né una verifica di durata**.
Grasso, tenute, spallamenti, tolleranze, distanziali e serraggio restano aperti.
La pagina SKF indica assenza di lubrificante/tenute: non presumere fornitura ingrassata.

### Albero e calore

Il solido Ø12 da−181 a−85 rappresenta solo il tratto freddo: non un albero
costruttivo. Con momenti sovrapposti@@BENDING_MOMENT@@Nm, tensione nominale
di flessione@@BENDING_STRESS@@MPa e von Mises@@VM_STRESS@@MPa, senza intagli,
fatica, materiale/temperatura ammissibili o accoppiamenti: nessun esito di resistenza.
Il segmento47mm con incastro rigido ipotetico ed E190GPa dà@@STUB_DISP@@mm
di spostamento al bordo dovuto al solo momento. Non include tratto caldo,
cuscinetti, carrier/telaio, deformazioni termiche né l'intero disco.
**Non confrontarlo col gioco V4 per dichiarare assenza di contatti.**

Q=kAΔT/L con k20, ΔT300 eL80mm:@@SHAFT_HEAT@@W per albero.
Due fasi a corrente RMS1,68 eR1,8Ω: riferimento rame@@COPPER@@W per motore.
Sono sorgenti di screening, non temperature o un bilancio del vano.
Motore ambiente max50°C, driver40°C, cinghia80°C: limiti differenti.
Driver fuori vano in quadro distinto da dimensionare, outdoor non qualificato.
Misurare anche il picco durante il raffreddamento; non basta misurare l'aria.

PROMASIL-1000L: candidato grado50, non struttura portante. Dati tipici
2018-04: densità300, cp1020, λ0,081/0,099/0,126/0,163 a temperature MEDIE
200/400/600/800°C; ritiro0,5% a1000°C/12h. Compressione a freddo>2,5MPa
non dimostra creep/portanza a caldo. SDS US non sostituisce SDS Italia;
nessuna polvere/fibra esposta ad alimenti/fumi. Carrier caldo15 non integrato.

## Manutenzione e connessioni da chiudere

Coordinate V4, origine piano z0. Vano[−245;−85], inviluppo[−221;−85].
La piastra motore è sul fronte del riduttore, non avvitata alla cassa posteriore.
Albero minimo19, puleggiaL21 collocata da−125 a−104: ingaggio geometrico
minimo@@ENGAGEMENT@@, ma il vero calettamento/mozzo, ritenzione e accesso viti non sono verificati.
I foriØ8/Ø12 delle pulegge sono lavorazioni PROPOSTE, non fori forniti o tolleranze assegnate.

Per il passaggio frontale[−237;−93], il cassetto in quota non passa.
Con disco/carrier previamente sostenuti e scollegati, schermo solidale al
cassetto, abbassamento12: estremi[−233;−97], margini verticali1/1 dopo3
per bordo. Nel vano restano2 oltre riserva inferiore10. **Margine troppo
ridotto per congelare il montaggio senza stack di tolleranze**.
Schermo fisso o giunto che non si libera con12 renderebbero il percorso invalido.

La traslazione per liberare l'intera profondità è465,5, non300.
La sporgenza finale davanti alla pelle y−167,5 è183, inferiore allo spazio
riservato300; quest'ultimo è spazio davanti al forno, non corsa del cassetto.
Guide, struttura sotto piano, traversi, carter, apertura viti, connettori,
peso reale e appoggio del gruppo sfilato non sono integrati. Nessuna
dimostrazione di manutenzione o alternativa dal basso sull'appoggio fisso.

## CAD e riproducibilità

- `../fonti/PG5_fornitore.STEP` e WGA sono file originali distinti dal modello C03.
- `../cad/modulo_freddo_C03_NON_ESECUTIVO.step`: motore ruotato180° suX e traslato, con20 inviluppi, senza cinghia solida, viti, sedi complete, giunto e percorso caldo. Non inviare in produzione come disegno esecutivo.
- `audit_CAD.json`: importazioni, unità, volumi geometrici (NON peso), trasformazione, hash, esclusioni e rilettura. Inviluppi di catalogo senza denti sovrastimano volutamente le flange.
- `index.html`: visualizzazione del solo modulo sinistro, schemi dei due moduli e documenti, senza CDN/server. L'occultamento dello schermo è solo grafico.
- `registro_banco_freddo.csv`: tutte le misure vuote, tutte le prove NON_ESEGUITE.
- @@TEST_COUNT@@ test software C03 superati; controllano formule, fonti, artefatti e limiti dichiarati, non il forno fisico.

Il build controlla hash del CAD e degli ingressi: se cambiano layout,
componenti, codice geometrico o numerico, occorre ripetere prima l'audit CAD.
PDF/PNG richiedono esportazione dopo il build; `esportazione.json` lega le
anteprime ai relativi HTML/SVG e non equivale a revisione tecnica.

## Gate successivo

1. Riesaminare richieste tecniche e acquisire conferme aggiornate: coppia2/3, radiale al pignone, servizio50°C/IP, driver/corrente, grasso/precarico e dati del pannello. Nessun invio automatico.
2. Definire il percorso dei carichi caldo/freddo, supporto pietra e giunto; completare sedi, ritenzioni, guide, montaggi e passaggi, con tolleranze ed eventuale aumento del vano/apertura motivato.
3. Banco protetto di un modulo a freddo, solo dopo riesame e soglie scritte: coppia/regolarità, carichi/momento, detriti, manutenzione e guasti.
4. Campione caldo strumentato dopo dimensionamento/riesame; aria/fumi e camino seguono il piano C02, non sono approvati dalla scelta dei motori.
5. Forno completo, tre avvii da freddo, due pizze simultanee e cinque doppie infornate; sicurezza e durata prima della preserie.

## Fonti pubbliche archiviate

@@SOURCE_LIST@@

Documenti disponibili il03/10/2026, non conferme di disponibilità commerciale
o di attualità per il lotto futuro. Fonti proprietarie mantenute localmente,
nessuna pubblicazione o redistribuzione del dossier effettuata.
