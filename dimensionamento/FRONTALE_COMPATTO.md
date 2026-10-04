# Variante frontale compatta — studio geometrico

Questa variante conserva il piano di cottura in cordierite di **79 × 41 cm**, le due piastre rotanti di **Ø 32 cm** e la zona legna posteriore di **25 cm**. Cambia solo il fronte: l'avancorpo passa da 25 a **8 cm**. La profondità dalla porta al fondo diventa quindi **74 cm**, contro i **91 cm** della variante precedente.

Le successive [verifiche geometriche e della rete di pressione](results/VERIFICHE_COMPATTA.md) riportano ipotesi, risultati e limiti del tiraggio. La sovrapposizione del raccordo alle pizze nella vista dall'alto è ammessa; resta da dettagliare il collettore in quota.

Le quote usano `y = 0` sul bordo iniziale del piano di cottura; i valori negativi sono davanti al piano.

| Elemento | Variante precedente | Variante compatta |
|---|---:|---:|
| Avancorpo davanti al piano | 25 cm | 8 cm |
| Piano + focolare posteriore | 66 cm | 66 cm |
| Profondità porta–fondo | 91 cm | 74 cm |
| Piano della porta | -25 cm | -8 cm |
| Bordo anteriore delle piastre rispetto alla porta | 29,5 cm | 12,5 cm |
| Centro delle piastre rispetto alla porta | 45,5 cm | 28,5 cm |

## Disposizione proposta

La porta è sul piano `y = -8 cm`. Il vano resta continuo dalla porta alla camera: in questa variante non c'è un architrave interno né una seconda battuta a `y = 0`.

L'asse del camino è a `y = +4,5 cm`, ossia 4,5 cm dietro l'inizio del piano e 12,5 cm dietro la porta. La distanza porta–asse camino mantiene dunque i **12,5 cm** già previsti; il camino arretra sopra il piano, invece di richiedere un vestibolo profondo 25 cm.

La bocca candidata resta larga **72 cm** per servire le due piastre. Sopra il suo fronte va previsto un adattatore su volta che raccoglie i fumi verso il camino. Forma, altezze interne e perdite di carico dell'adattatore non sono fissate qui: sono da progettare e verificare separatamente.

## Raccordo in quota, non sul pavimento

Le quote di lavoro sono tubo con diametro interno **Ø 13 cm** e raccordo/flangia di diametro esterno **Ø 19 cm**, entrambe ipotesi di progetto. Con l'asse a `+4,5 cm`, l'ingombro proiettato del raccordo va da `y = -5 cm` a `y = +14 cm`.

Il raccordo non deve essere contenuto nell'avancorpo come volume a pavimento: va sostenuto nella parte alta della cappa/volta. Il suo bordo anteriore rimane a 3 cm dalla porta (`-5 cm` rispetto a `-8 cm`). Con i margini ipotizzati, l'inviluppo da riservare sul tetto va da `y = -8 cm` a `y = +17 cm`: 3 cm davanti al raccordo e 3 cm oltre il suo bordo posteriore. Questo non dimensiona l'appoggio strutturale né le distanze termiche.

In proiezione dall'alto il raccordo Ø19 si sovrappone leggermente ai contorni anteriori interni delle piastre; il foro Ø13 resta fra i due dischi, nella fascia iniziale del piano. **La sovrapposizione in pianta con piastre o pizze è ammessa:** non impone di spostare il camino davanti a esse. Sono elementi della copertura, separati verticalmente dal piano. Vanno verificate la quota inferiore dell'eventuale collettore, l'accesso con la pala e la distribuzione di calore e fumi, non l'assenza di sovrapposizione nel disegno dall'alto.

## Perché cambia il vincolo

Nel disegno precedente si era imposto che il raccordo Ø19 più 3 cm di margine davanti e dietro stesse tutto nel vestibolo sul pavimento. Questo porta artificialmente a circa 25 cm di avancorpo. Il raccordo invece è un elemento alto, appartenente a cappa e volta; non è una porzione del piano su cui devono stare le pizze.

La variante compatta non sostiene che il camino possa attraversare il piano: il piano rimane continuo. Indica soltanto la sua proiezione e l'area di tetto necessaria per raccordarlo alla presa alta anteriore.

## Limiti da verificare prima del progetto costruttivo

Questa è un'analisi geometrica. Non dimensiona la sezione del collettore, le fessure, il plenum, le prese d'aria o la potenza del fuoco.

Con una bocca larga 72 cm e due piastre, la cattura dei fumi può essere disuniforme fra lato sinistro e destro; inoltre le piastre sono proiettate molto vicine alla presa fumi. Tiraggio, distribuzione dei fumi, comportamento con porta aperta o chiusa e ricambio d'aria devono essere verificati con un prototipo e prove di fumo/pressione, oppure con un'analisi fluidodinamica adeguata.

Il modello termico V3 esistente non fornisce una previsione valida per questa nuova configurazione di aria e cappa.

I prodotti Ooni Karu sono un riferimento utile per osservare un forno compatto con gestione di fiamma e aria, ma le nostre quote non sono attribuite a Ooni: i materiali pubblici usati non forniscono una quota certa fra porta, pietra e asse del camino per questa configurazione a due piastre.

Fonti di confronto consultate:

- [Ooni Karu 2 Pro](https://ooni.com/products/ooni-karu-2-pro) — descrive FlameKeeper e le regolazioni dell'aria.
- [Disegno dimensionale Ooni Karu 16](https://www.webstaurantstore.com/documents/specsheets/ooni_karu_16-oven_dimensions.pdf) — disegno tecnico del produttore, utile come riferimento visivo ma non come origine delle quote sopra.

## File e riproduzione

In MATLAB, dalla cartella `dimensionamento`, eseguire `s = run_compact_front_study();`. I parametri `c.frontDepth` e `c.flueY` si trovano all'inizio dello script; la funzione `oven_compact_front_geometry` calcola e controlla gli ingombri. Le sette verifiche eseguite controllano quote e rifiuto di un raccordo troppo avanzato, non il comportamento dei fumi.

- [Confronto delle sezioni](results/confronto_frontale_compatto.png)
- [Pianta compatta](results/pianta_frontale_compatto.png)
- Parametri e geometria: `results/fronte_compatto.mat`.
