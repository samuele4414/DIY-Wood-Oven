# Sensibilità alla discretizzazione — riferimento V4

Confronto a 40 e 25 mm dello stesso riferimento, alle stesse condizioni imposte. Due maglie grossolane non dimostrano indipendenza dalla griglia. Cambiano anche l’approssimazione a gradini del camino, della volta e lo spessore risolto della pizza (una cella): sono tutti contributi dell’errore geometrico/numerico.

| Aspirazione | Stato 40 / 25 mm | Canna g/s, 40 / 25 mm | Gas sopra pizze °C, 40 / 25 mm |
|---|---|---|---|
| Anteriore | running / running | 18.48 / 10.95 | 260, 272 / 84, 95 |
| Centrale | not_run / not_run | — / — | — / — |

Le differenze misurate vanno lette insieme alle aree effettive delle aperture e alla variabilità temporale. Una piccola differenza tra queste due maglie non certifica accuratezza; una differenza grande esclude l’uso del solo confronto grossolano per stabilire quote costruttive.

Le sonde sono richieste alla stessa quota di 100 mm. La sezione visualizzata segue invece la quota dei nodi effettivi del file FDS, registrata nel JSON. Non confondere la temperatura del gas con quella della pizza.
