# DIY Wood Oven — modello V2

Variante parametrica del modello V1, con lo stesso diagramma Simulink e cinque
stati: temperatura del piano, della volta, dei gas e della pizza, più la massa
d'acqua nella pizza.

La V2 aumenta la portata di legna da 0,0005 a 0,00131 kg/s e aggiunge il
parametro `T_floor_target = 450 + 273.15` K. Il modello non utilizza questa
variabile: non introduce un controllo automatico né garantisce il raggiungimento
di 450 gradi Celsius.

Restano gli scambi e i bilanci della V1: combustione, convezione tra gas e
superfici, scambio piano-pizza, irraggiamento dalla volta, dispersioni,
perdite al camino ed evaporazione dell'acqua.

## File della versione

- `oven_model.slx`: diagramma Simulink V1 riutilizzato senza modifiche.
- `oven_parameters.m`: geometria, proprietà termiche, condizioni iniziali e
  parametri di combustione, camino e pizza della V2.
- `.gitignore`: esclusione delle cache e dei file temporanei.

Non è disponibile un file `.slx` distinto per la V2. Il modello e i parametri
sono copie identiche dei file disponibili `oven_model_V1.slx` e
`oven_parameters_V2.m`, rinominati per mantenere percorsi stabili nel repository.
Lo script conserva le etichette originali obsolete: `MODEL V0` nell'intestazione
e `PIZZA OVEN V1` nella stampa a schermo. Questo README identifica la versione
parametrica effettiva.

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
| Portata di legna | 0,00131 kg/s, pari a 4,716 kg/h |
| Potere calorifico / rendimento effettivo | 15 MJ/kg / 0,70 |
| Potenza effettiva di combustione | 13755 W |
| Obiettivo dichiarato per il piano | 450 gradi Celsius; variabile non utilizzata dal modello |
| Camino | Diametro interno 100 mm, altezza 500 mm |
| Pizza rappresentata | Una, diametro 320 mm, massa 250 g |
| Acqua iniziale nella pizza | 150 g |

Le quote e le ipotesi appartengono alla bozza V2. Il modello non rappresenta
ancora due piastre rotanti separate e non è un dimensionamento costruttivo
validato del forno completo.

Questa versione combina il diagramma V1 e i parametri V2 oggi disponibili.
Il modello sorgente è stato salvato il 21 settembre 2026, dopo gli script dei
parametri del 20 settembre: non è verificabile che il diagramma coincida
esattamente con quello delle prime fasi storiche V1 e V2.

## Cronologia delle versioni

Ogni versione viene registrata con un commit separato. Il modello e i parametri
attivi vengono aggiornati negli stessi percorsi: le versioni precedenti restano
consultabili nella cronologia Git, senza cartelle o ZIP di backup.

Report e immagini vengono conservati con il numero della versione nel nome.

La V0 è conservata nel commit `35cda97` e la V1 nel commit `fe674e3`.
Non sono stati individuati report o immagini separati attribuibili alla V2;
quelli delle versioni successive
non vengono inclusi in questo passaggio.
