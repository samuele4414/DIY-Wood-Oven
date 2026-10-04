# Studio CFD 01 — risultati effettivi

Famiglia di calcolo: `coarse_dx40_t30`. Solo i casi indicati come completati hanno raggiunto il tempo richiesto con arresto normale del solutore.

**Studio esplorativo, non validato sperimentalmente né indipendente dalla maglia.** Le temperature riportate sono del gas. La pizza è una superficie a 100 °C imposti: il calcolo non ne prevede la temperatura né i secondi di cottura.

## Geometrie

| Caso | Pizze | Ingombro interno cm | Zona legna m² | Minimo spazio fra pizze/piatti cm |
|---|---:|---|---:|---:|
| C1 | 2 | 79 × 74 | 0.163 | 5.0 |
| C2 | 3 | 79 × 79 | 0.090 | 4.8 |
| C3 | 3 | 106 × 74 | 0.265 | 4.0 |
| C4 | 3 | 110 × 75 | 0.208 | 3.0 |
| C5 | 3 | 100 × 92.7 | 0.087 | 4.0 |
| C6 | 2 | 90 × 80 | 0.065 | 2.0 |

## Output CFD

Flussi in g/s. La bocca può avere contemporaneamente ingresso e uscita: vengono mantenuti distinti. Il flusso totale di aria/gas non equivale alla percentuale di cattura del fumo.

| Caso | Aspirazione | Stato | Tempo s | HRR medio kW | Bocca ingresso | Bocca uscita | Canna uscita | Gas sopra pizze °C |
|---|---|---|---:|---:|---:|---:|---:|---|
| C1 | Anteriore | completed | 30.0 | 18.75 | 30.19 | 12.34 | 18.49 | 260 / 277 |
| C1 | Centrale | completed | 30.0 | 18.79 | 30.88 | 13.34 | 18.28 | 267 / 238 |
| C2 | Anteriore | completed | 30.0 | 18.73 | 31.15 | 13.01 | 18.76 | 256 / 326 / 325 |
| C2 | Centrale | completed | 30.0 | 18.72 | 31.38 | 13.32 | 18.62 | 319 / 304 / 282 |
| C3 | Anteriore | completed | 30.0 | 18.74 | 37.73 | 19.80 | 18.68 | 289 / 222 / 247 |
| C3 | Centrale | completed | 30.0 | 18.73 | 38.12 | 20.27 | 18.46 | 264 / 245 / 254 |
| C4 | Anteriore | completed | 30.0 | 18.77 | 29.16 | 13.40 | 16.61 | 239 / 311 / 332 |
| C4 | Centrale | completed | 30.0 | 18.76 | 31.06 | 13.20 | 18.63 | 264 / 274 / 331 |
| C5 | Anteriore | running | 7.70886 | 10.43 | 10.16 | 15.71 | 11.38 | 135 / 178 / 188 |
| C5 | Centrale | non eseguito | — | — | — | — | — | — |
| C6 | Anteriore | non eseguito | — | — | — | — | — | — |
| C6 | Centrale | non eseguito | — | — | — | — | — | — |

## Interpretazione e limiti

- Le sezioni del visualizzatore sono medie dei file binari FDS realmente prodotti. La finestra effettiva e la quota compaiono nel risultato JSON. Non sono colori assegnati al disegno per simulare un risultato.
- La volta, il piano e le pareti della canna hanno temperatura prescritta; l’energia scambiata con queste superfici non è limitata dalla sola potenza del bruciatore. Si confrontano condizioni di esercizio imposte, non rendimento energetico o riscaldamento da freddo.
- I piatti circolari sono fermi nel calcolo del gas. La rotazione nella vista 3D è meccanica e illustrativa; non costituisce una simulazione della cottura di una pizza in movimento.
- La maglia grossolana altera aree, curvature e altezza effettiva delle aperture; i metadati documentano le sezioni risolte. La maglia deve essere raffinata prima di dimensionare il camino.
- I valori di gas sopra le pizze sono sonde puntuali richieste a quota 100 mm dal piano, campionate nelle celle FDS corrispondenti: non sono temperature della pizza né flussi termici completi. Non bastano per scegliere la migliore uniformità di cottura.
- La durata breve e le fluttuazioni LES non dimostrano convergenza statistica. Le differenze tra finestre temporali successive sono disponibili nel JSON.
- Stessa quota di uscita camino, 1280 mm dal piano. Bocca aperta, assenza di vento, fuoco prescritto equivalente a 18,75 kW lordi. Porte e carico della legna non vengono manovrati.
- Per scegliere acciaio isolato/refrattario e temperatura della scocca serve aggiungere conduzione, proprietà dipendenti dalla temperatura e spessori; nessun risultato attuale dimostra che la scocca resti fredda.

Il confronto geometrico identifica C2 come variante compatta per tre pizze; la pizza posteriore resta da verificare con la pala. C3 offre tre posizioni in fila con una bocca più larga. Queste sono considerazioni geometriche, non una graduatoria CFD.

Metodo e fonti: [CFD_METHOD.md](../docs/CFD_METHOD.md), [manuali ufficiali FDS/Smokeview](https://pages.nist.gov/fds/manuals.html).
