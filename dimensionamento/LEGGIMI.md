# Dimensionamento preliminare — bocca, cappa e focolare

La geometria compatta e le verifiche preliminari sono raccolte nella [V4 per il design](../v4/README.md), con scheda PDF, pianta CAD nominale e parametri. Volta, forma del focolare e ingombri esterni restano da sviluppare.

**Aggiornamento del fronte:** la [variante compatta](FRONTALE_COMPATTO.md) confronta un avancorpo di 8 cm con i 25 cm di questo primo studio, portando il raccordo sopra l'inizio del piano. Le quote e i risultati termici sotto appartengono allo studio precedente e non validano il nuovo percorso dei fumi.

Le [verifiche preliminari della variante compatta](results/VERIFICHE_COMPATTA.md) aggiungono una rete di pressione con presa posteriore, bocca bidirezionale e sensibilità a camino e vento. Esecuzione: `s = run_draft_checks();`. È un calcolo distinto dalla V3 e non costituisce una validazione sperimentale della captazione.

Questo studio continua il modello V3 mantenendo il piano in cordierite da **79 × 41 cm** e i due dischi da **32 cm**. Usa ciocchi lunghi **25 cm**, come indicato dall'utente. Le nuove quote formano un candidato geometrico modificabile: non derivano ancora da misure di un prototipo.

## Proposta da confrontare

| Elemento | Quota interna di riferimento | Motivazione |
|---|---:|---|
| Tratto anteriore sotto la cappa | 25 cm | Contenere un raccordo di ingombro 19 cm con 3 cm liberi davanti e dietro |
| Piano con dischi | 79 × 41 cm | Vincolo del progetto |
| Zona legna posteriore | basi 79 / 51 cm, profondità 25 cm | Spazio per due file trasversali, nelle ipotesi sotto |
| Lunghezza complessiva in pianta | 25 + 41 + 25 = 91 cm | Cappa + piano + focolare; rivestimenti esterni esclusi |
| Volta, altezza al centro | 28 cm | Candidato confrontato con 25 e 30 cm |
| Volta, altezza alle pareti | 19 cm | Con sezione parabolica e freccia 9 cm |
| Passaggio della camera / apertura della porta esterna | 72 × 16 cm | Accesso rettilineo ai due dischi con pala ipotizzata larga 34 cm |
| Botola posteriore | 30 × 14 cm | Inserimento di un ciocco da 25 cm già orientato trasversalmente |
| Camino, diametro interno | 13 cm, confronto con 15 cm | Variabile della rete di tiraggio, non scelta definitiva |
| Camino, altezza efficace | 1 m, confronto con 0.5 m | Variabile della rete di tiraggio |

L'ingombro del raccordo e la sezione dei ciocchi sono ancora **ipotesi**, rispettivamente 19 cm e 7 cm. Le quote devono essere aggiornate quando saranno scelti tubo/raccordo e legna reali. I 3 cm attorno al raccordo sono un margine geometrico del disegno, non una distanza termica o prescrizione antincendio.

## Perché aggiungere spazio davanti

Nel disegno precedente il camino era rappresentato come una proiezione, senza un volume fisico di raccolta. Il nuovo schema separa la camera calda dalla cappa anteriore e contiene interamente anche l'ingombro del raccordo. Il requisito geometrico è:

`profondità cappa >= ingombro raccordo + margine anteriore + margine posteriore`.

Con le ipotesi attuali: `19 + 3 + 3 = 25 cm`. Usare solo il diametro interno del tubo sottostimerebbe l'ingombro. L'asse del camino si trova a metà di questa zona: **12.5 cm davanti alla bocca della camera e 12.5 cm dietro al fronte esterno**. Questo verifica il contenimento in pianta; restano da progettare la transizione, il raccordo verticale e il sostegno del camino.

L'organizzazione con presa dei fumi davanti alla camera e piano di ingresso sotto la presa è descritta anche da [Forno Bravo](https://www.fornobravo.com/pompeii-oven/oven-overview/). La fonte supporta la disposizione generale, non le nostre quote di 25 cm o il diametro di 13 cm.

## Dove si trova la porta

La battuta della porta è sul **fronte esterno**, prima della raccolta fumi procedendo dall'esterno verso l'interno. La sequenza è: **porta → cappa con presa del camino → camera con due pizze → focolare posteriore**. Questa disposizione recepisce la correzione geometrica richiesta dall'utente.

1. **Ingresso esterno e battuta della porta**, sul fronte del tratto aggiunto, alla coordinata `doorSeatY = entranceY = -hoodDepth = -0.25 m`. L'apertura della porta è larga 72 cm e alta 16 cm.
2. **Passaggio della camera**, al bordo del piano da 79 × 41 cm, alla coordinata `y=0`, largo 72 cm e alto 16 cm. Resta permanentemente aperto verso la cappa: qui non è prevista una porta, che isolerebbe la camera dal camino.

L'asse del camino è **12.5 cm verso l'interno rispetto alla porta**. Il bordo anteriore dei dischi è a 4.5 cm dentro la camera: la distanza dalla porta a quel bordo è quindi **29.5 cm**, mentre i centri dei dischi sono a **45.5 cm** dalla porta. I 25 cm aggiunti appartengono alla cappa anteriore.

Chiudendo questa porta, il collegamento geometrico fra camera e camino rimane aperto. **Il funzionamento a porta chiusa non è però simulato:** la V3 conserva l'ingresso d'aria imposto e la rappresentazione della bocca aperta. L'alimentazione dell'aria di combustione con porta chiusa deve essere dimensionata separatamente; la disposizione geometrica non dimostra il funzionamento con chiusura ermetica.

Per depositare la pizza avanzando dritto verso ciascun disco, la bocca deve lasciare passare l'utensile quando è allineato a entrambi i centri. Nel nostro caso:

`larghezza minima = 37 cm fra i centri + 34 cm pala + 2 × 0.5 cm margine = 72 cm`.

Il confronto con una bocca da 60 cm resta previsto: richiederebbe un ingresso inclinato o una manovra laterale, che questa verifica rettilinea non dimostra possibile. Le pareti e il telaio residui ai lati della bocca da 72 cm devono essere dimensionati strutturalmente. La pala reale va misurata, incluse forma e manico.

## I 14 cm del trapezio sono sufficienti?

La misura è la **profondità del trapezio in pianta**, non l'altezza verticale della camera. Un ciocco lungo 25 cm può stare anche in un focolare profondo 14 cm se il suo asse è disposto trasversalmente alla larghezza: non è corretto confrontare direttamente lunghezza del ciocco e profondità senza precisare l'orientamento.

Con pezzi di sezione ipotizzata 7 cm e gli spazi indicati nel disegno:

- una fila occupa `4 cm davanti + 7 cm legna + 3 cm dietro = 14 cm`;
- due file occupano `4 + 7 + 3 fra le file + 7 + 3 = 24 cm`.

Il focolare da **25 cm** offre quindi due file e 1 cm di riserva geometrica. I 14 cm della bozza possono contenere una fila, ma lasciano poco margine per variare disposizione, braci e accumulo di cenere. Non si tratta di una stima della potenza del fuoco: aerazione, quantità di legna e altezza della fiamma devono ancora essere verificate.

Nel candidato la prima fila di legna inizia 4 cm dietro la fine del piano. Sommati ai 4.5 cm fra dischi e fine piano, risultano **8.5 cm fra il bordo posteriore dei dischi e l'inizio nominale della legna**. Non equivale alla distanza dalla fiamma. L'eventuale fermalegna/parabraci non è ancora dettagliato.

Le larghezze 79 e 51 cm del trapezio permettono la disposizione trasversale dei ciocchi da 25 cm nello scenario disegnato. Inserirli longitudinalmente con margini davanti/dietro richiederebbe invece almeno **32 cm** di profondità, nelle medesime ipotesi.

## Altezza della volta e della bocca

Il riferimento passa a 28 cm al centro e 19 cm alle pareti, con bocca alta 16 cm. Lo studio confronta altezze centrali di 25, 28 e 30 cm mantenendo l'imposta a 19 cm: cambiano freccia, volume e superficie della volta. Non viene applicata una proporzione universale fra altezza della bocca e della volta.

I pesi radiativi e i coefficienti convettivi della V3 restano imposti: non sono ricalcolati geometricamente per ogni volta. I 28 cm sono quindi una quota candidata compatibile con gli ingombri, non un'altezza termicamente ottimizzata.

Come confronto di scala, le specifiche ufficiali [Gozney Dome Gen 2](https://help.gozney.com/hc/en-us/articles/40182279889553-What-are-the-specifications-of-Dome-Gen-2-Series) riportano altezza interna di 226 mm e apertura alta 133 mm; la versione XL riporta 238 e 140 mm. Sono geometrie diverse e non giustificano il trasferimento automatico delle loro quote a questo forno largo 790 mm, con due dischi fissi nelle rispettive posizioni.

## Confronto termico a pari temperatura del piano

La V3 caricava le pizze dopo un tempo uguale. Ora ogni configurazione viene preriscaldata fino a una **media dei nodi superiori dei dischi di 450 °C**, usata come riferimento comune della bozza. Il preriscaldamento è limitato a 120 minuti; se una configurazione non raggiunge il riferimento, il risultato viene indicato esplicitamente e la cottura non viene simulata.

Raggiunta la soglia, vengono inserite due pizze per 90 secondi. Non viene imposto che volta, gas e strato inferiore della pietra siano uguali: lo studio registra anche queste temperature. La potenza e i coefficienti del modello restano invariati fra i casi salvo il parametro esplicitamente confrontato.

Al confronto delle dimensioni si aggiungono due prove mirate: consumo imposto di 4.5 kg/h anziché 3.5 e, successivamente, pietra da 20 mm anziché 10 mm mantenendo 4.5 kg/h. La seconda prova va confrontata con la prima per isolare lo spessore. Il parametro V3 dello spessore è comune a piano fisso, dischi e focolare: questa variazione raddoppia tutte queste masse, non soltanto i dischi. Il consumo maggiore è uno scenario energetico, non una carica di legna già dimensionata o validata.

I risultati mostrano un limite quantitativo del carico pizza: il modello consuma quasi tutta l'acqua nei 90 secondi. Per questo non si devono usare i cali termici calcolati come previsioni attendibili del prototipo. Il confronto sul preriscaldamento a forno vuoto non contiene tale carico, ma conserva le incertezze su combustione, scambi e camino.

Questi sono confronti di sensibilità del modello, **non calibrazione sperimentale**. La zona anteriore aggiunta è verificata geometricamente ma **non viene ancora aggiunta come volume termico/fluidodinamico** ai bilanci V3. Il tiraggio usa ancora la temperatura della zona anteriore della camera: non include diluizione con aria esterna e raffreddamento nella cappa. La nuova posizione della presa non è pertanto convalidata dai grafici termici.

Il passo successivo per scegliere il camino è rappresentare cappa, perdite del raccordo e cattura del flusso in uscita dalla bocca; per chiudere le dimensioni del focolare occorrono sezione reale dei ciocchi, cariche e flusso d'aria. Materiali, supporti, dilatazioni e trasporto di umidità nella pizza restano le limitazioni documentate nella V3.

## Esecuzione e file

In MATLAB, dalla cartella `dimensionamento`:

```matlab
[p,d] = oven_dimension_defaults();
g = oven_dimension_geometry(p,d);
validation = validate_dimensions();
study = run_dimension_study();
draw_dimension_study(study);
write_dimension_report(study);
```

Per cambiare solo il raccordo e verificare l'ingombro:

```matlab
[p,d] = oven_dimension_defaults();
d.collarDiameter = 0.22;
d.hoodDepth = 0.28;  % 22 + 3 + 3 cm
g = oven_dimension_geometry(p,d);
```

Per un singolo confronto termico:

```matlab
[p,d] = oven_dimension_defaults();
p.geom.rearDepth = 0.30;
h = oven_preheat_target(p,d.targetPlateC,d.maxPreheatSeconds);
if h.reached
    p.sim.warmupSeconds = h.timeSeconds;
    r = oven_simulate(p);
end
```

`results/study.mat` contiene dati e parametri di tutti i casi; `summary.csv` conserva le misure del confronto; `pianta_quotata.png` e `sezioni_quotate.png` mostrano il candidato. I file in `model_v3` sono usati come dipendenza e mantengono la configurazione precedente.
