# DIY Wood Oven — modello V1

Modello termico del forno a legna con cinque stati: temperatura del piano,
della volta, dei gas e della pizza, più la massa d'acqua nella pizza.

Rispetto alla V0 comprende combustione della legna, convezione tra gas e
superfici, scambio piano-pizza, irraggiamento dalla volta, dispersioni del
piano e della volta, perdite al camino ed evaporazione dell'acqua.

## File della versione

- `oven_model.slx`: modello Simulink V1.
- `oven_parameters.m`: geometria, proprietà termiche, condizioni iniziali e
  parametri di combustione, camino e pizza della V1.
- `.gitignore`: esclusione delle cache e dei file temporanei.

Il modello e i parametri sono copie identiche dei file disponibili
`oven_model_V1.slx` e `oven_parameters_V1.m`, rinominati per mantenere percorsi
stabili nel repository. L'intestazione iniziale dello script conserva la
vecchia etichetta `MODEL V0`; la stampa a schermo identifica la V1.

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
| Altezza della camera | 250 mm |
| Volta in acciaio | Spessore 2 mm, area assunta uguale al piano |
| Temperatura ambiente e iniziale | 25 gradi Celsius |
| Portata di legna | 0,0005 kg/s, pari a 1,8 kg/h |
| Potere calorifico / rendimento effettivo | 15 MJ/kg / 0,70 |
| Potenza effettiva di combustione | 5250 W |
| Camino | Diametro interno 100 mm, altezza 500 mm |
| Pizza rappresentata | Una, diametro 320 mm, massa 250 g |
| Acqua iniziale nella pizza | 150 g |

Le quote e le ipotesi appartengono alla bozza V1. Il modello non rappresenta
ancora due piastre rotanti separate e non è un dimensionamento costruttivo
validato del forno completo.

Questa versione ricostruisce la V1 dai file oggi disponibili. Il modello
sorgente è stato salvato il 21 settembre 2026, dopo lo script dei parametri
del 20 settembre: non è verificabile che il diagramma coincida esattamente
con la primissima revisione storica V1.

## Cronologia delle versioni

Ogni versione viene registrata con un commit separato. Il modello e i parametri
attivi vengono aggiornati negli stessi percorsi: le versioni precedenti restano
consultabili nella cronologia Git, senza cartelle o ZIP di backup.

Report e immagini vengono conservati con il numero della versione nel nome.

La V0 è conservata nel commit `35cda97`. Non sono stati individuati report
o immagini separati attribuibili alla V1; quelli delle versioni successive
non vengono inclusi in questo passaggio.
