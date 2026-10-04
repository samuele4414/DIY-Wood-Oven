# Studio CFD 01 — geometrie alternative del forno

Pizze **Ø300 mm**, piatti rotanti **Ø320 mm**. Sei geometrie ideali con volta parabolica, ciascuna confrontata con aspirazione anteriore e centrale. Le quote sono **interne**: pareti, isolamento, rivestimento e telaio aumentano l'ingombro esterno.

| Caso | Pizze | Piatti | Ingombro interno in pianta, vestibolo incluso | Fuoco |
|---|---:|---|---|---|
| C1, riferimento V4 | 2 | Rotanti | 790 × 740 mm | Posteriore trapezoidale |
| C2, compatto | 3 | Piano fisso | 790 × 790 mm | Angolo posteriore sinistro |
| C3, in fila | 3 | Piano fisso | 1060 × 740 mm | Posteriore |
| C4, laterale | 3 | Piano fisso | 1100 × 750 mm | Fascia sinistra da 310 mm |
| C5, cerchio Ø1000 | 3 | Piano fisso | 1000 × 927 mm | Angolo sinistro |
| C6, cerchio Ø900 | 2 | Rotanti | 900 × 800 mm | Posteriore ridotto |

I cerchi sono troncati sulla corda anteriore da 720 mm. La bocca non è posta sulla tangente del cerchio: ciò produrrebbe un ingresso senza larghezza. Il vestibolo anteriore è profondo 80 mm. La volta ha imposta a 190 mm e culmine a 280 mm. Nei poligoni è una botte parabolica trasversale; nei cerchi è un paraboloide. C3 ha bocca larga 990 mm; gli altri casi 720 mm. Altezza nominale della bocca: 160 mm.

## Cosa viene confrontato

- Posizione effettiva dell'aspirazione dei gas, non soltanto posizione esterna del tubo: anteriore a y=45 mm oppure centrale.
- Canna nominale Ø130 mm, uscita a quota 1280 mm dal piano (1000 mm sopra il culmine della volta), aria esterna ferma. Il raccordo anteriore parte da 160 mm, quello centrale da circa 280 mm: l'altezza totale del condotto è rispettivamente 1120 e 1000 mm. La quota di uscita è mantenuta uguale nel confronto.
- Stessa potenza chimica prescritta, 18,75 kW, equivalente energetico di 4,5 kg/h con PCI 15 MJ/kg. Il bruciatore rettangolare è un proxy; non rappresenta ciocchi o pirolisi della legna.
- Superfici a temperatura imposta: volta/pareti 500 °C, piano 450 °C, pizza 100 °C, interno canna 200 °C, aria e facce esterne 25 °C. Sono ipotesi di confronto; **25 °C sulla faccia esterna non è un risultato sull'isolamento**.

Il calcolo del gas è FDS 6.11.1 (LES, densità variabile, irraggiamento). Le pizze sono ostacoli fissi; l'animazione a 2 giri/min mostra il meccanismo. Non viene risolta una parete mobile, né calcolata la cottura degli ingredienti. Un piatto circolare complanare non cambia la geometria occupata mentre ruota.

Il volume, la bocca e la posizione del fuoco variano tra configurazioni: un confronto tra C1 e C3 riguarda l'intero progetto. Solo la coppia anteriore/centrale della stessa geometria è una variazione isolata della posizione del camino, fatte salve le differenze di discretizzazione.

## File e riproduzione

- `cases.json`: quote, posizioni, temperature e ipotesi condivise.
- `check_geometry.py`: controlli geometrici di distanza tra pizze/dischi, pareti e zona legna.
- `fds_writer.py`: genera la geometria discretizzata e le condizioni al contorno FDS.
- `run_study.py`: genera ed esegue i casi, uno alla volta, con log e identificativo SHA-256 dell'input.
- `postprocess.py`: legge output effettivi, CSV e sezioni binarie FDS.
- `inputs/`: input riproducibili e metadati della maglia.
- `results/`: risultati ridotti e controlli geometrici; consultare il rapporto per lo stato effettivo delle simulazioni.
- `runs/`: output voluminosi locali, esclusi da Git. I file `.smv` si aprono in Smokeview insieme agli output dello stesso caso.
- `docs/CFD_METHOD.md`: metodo, fonti e limiti.

Occorrono Python 3 con NumPy e FDS. Il runtime FDS è esterno alla repository. Il parametro `--fds` può indicare l'eseguibile locale `fds_openmp.exe`. Su questa macchina il runtime ufficiale è stato estratto nella cache dell'utente; nessuna installazione di sistema è richiesta.

```powershell
python cfd/check_geometry.py
python cfd/run_study.py --generate-only --dx 0.04 --seconds 30 --tag coarse
# Tutte le configurazioni, prima griglia grossolana:
python cfd/run_study.py --dx 0.04 --seconds 30 --threads 2 --tag coarse
# Sensibilità alla maglia del riferimento V4:
python cfd/run_study.py --case c1_v4_two_rotating --flue both --dx 0.025 --seconds 30 --threads 2 --tag refined
python cfd/collect_results.py --family coarse_dx40_t30
```

La prima maglia da 40 mm risolve il diametro del camino con circa tre celle: serve per uno screening molto grossolano delle dodici configurazioni. Il riferimento V4 viene confrontato anche a 25 mm, circa cinque celle sul diametro. Anche questa verifica resta grossolana e non basta per fissare le dimensioni costruttive del tiraggio. Una graduatoria richiede tempo sufficiente, verifica del bilancio di massa e della potenza effettiva, ulteriore sensibilità alla maglia e poi misure fisiche. Acciaio isolato e refrattario richiedono un modello termico dei materiali separato o accoppiato: queste superfici a temperatura prescritta non permettono di scegliere l'isolamento.

## Vincoli che la capacità geometrica non risolve

In C2 e C5 la pizza posteriore non ha un corridoio rettilineo libero fra quelle anteriori; serve verificare una manovra inclinata/sollevata con la pala reale. C4 richiede analoga verifica di servizio. C6 riduce molto la zona legna: i ciocchi da 250 mm devono essere trasversali e l'autonomia resta da valutare. Il materiale resistente alla fiamma e il materiale isolante hanno funzioni diverse; nessuna di queste quote include lo spessore definitivo della stratigrafia.

Fonti del solutore: [manuali NIST FDS/Smokeview](https://pages.nist.gov/fds/manuals.html), [rilascio FDS 6.11.1](https://github.com/firemodels/fds/releases/tag/FDS-6.11.1).
