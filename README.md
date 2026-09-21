# DIY Wood Oven — modello V0

Prima bozza del modello matematico del forno a legna, conservata con il modello
Simulink e i parametri originali. Questa versione descrive il riscaldamento del
piano di cottura con una potenza termica imposta.

## File della versione

- `oven_model.slx`: modello Simulink V0.
- `oven_parameters.m`: geometria, proprietà termiche, condizioni iniziali e
  potenza di riscaldamento della V0.
- `.gitignore`: esclusione delle cache e dei file temporanei.

## Avvio

Servono MATLAB e Simulink; il file è stato salvato con R2026a. Impostare questa
cartella come cartella corrente di MATLAB, quindi eseguire:

```matlab
run('oven_parameters.m');
open_system('oven_model.slx');
```

Premere **Run** nella finestra Simulink per avviare la simulazione, impostata
su 3600 secondi. Il modello non carica automaticamente i parametri: eseguire
lo script prima della simulazione.

## Parametri della bozza

| Grandezza | Valore |
| --- | --- |
| Piano anteriore | 790 x 410 mm |
| Zona posteriore trapezoidale | Basi 790 / 510 mm, profondità 140 mm |
| Spessore della cordierite | 10 mm |
| Temperatura ambiente e iniziale | 25 gradi Celsius |
| Potenza termica imposta | 5000 W |
| Coefficiente globale di perdita del piano | 8 W/K |

Le quote e le ipotesi appartengono alla bozza V0. Non sono un dimensionamento
costruttivo validato del forno completo.

## Cronologia delle versioni

Ogni versione viene registrata con un commit separato. Il modello e i parametri
attivi vengono aggiornati negli stessi percorsi: le versioni precedenti restano
consultabili nella cronologia Git, senza cartelle o ZIP di backup.

Report e immagini vengono conservati con il numero della versione nel nome.

Non sono stati individuati file di risultati separati attribuibili alla V0.
