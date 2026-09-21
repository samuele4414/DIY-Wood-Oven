# Confronti preliminari forno V3

Generato: 21-Sep-2026 11:28:47.

Modello non calibrato. Le temperature delle pizze sono medie di nodi equivalenti; non descrivono la doratura, il cornicione o una pizza cotta. Nessuna configurazione viene dichiarata ottimale o pronta per la costruzione.

Condizioni comuni: 3.5 kg/h di legna, PCI 15.0 MJ/kg, efficienza 0.70; 10.2 kW introdotti nel modello. Riscaldamento 30 minuti, due pizze da 30 cm e 250 g per 90 s, poi 90 s di recupero a fuoco acceso.

Piano fisso 0.1610 m²; due dischi 0.1608 m²; giochi 0.0020 m²; totale 0.3239 m².

| Caso | Dischi al carico °C | Base pizza 90 s °C | Sopra pizza 90 s °C | Escursione settori K | Acqua per pizza a 90 s, g | Massa guscio kg |
|---|---:|---:|---:|---:|---:|---:|
| Acciaio riferimento | 569.2 | 329.3 | 301.9 | 7.32 | 0.00 | 12.8 |
| Refrattario 30 mm | 263.7 | 102.0 | 102.0 | 0.00 | 75.06 | 51.8 |
| Volta piana | 548.2 | 306.8 | 276.3 | 5.58 | 0.00 | 15.1 |
| Focolare profondo 24 cm | 510.9 | 262.6 | 225.6 | 4.39 | 0.00 | 14.3 |
| Camino diametro 13 cm | 453.3 | 175.8 | 142.0 | 6.75 | 0.00 | 12.8 |
| Camino alto 1 m | 488.6 | 230.7 | 189.7 | 6.48 | 0.00 | 12.8 |
| Camino posteriore | 484.9 | 230.5 | 192.2 | 10.21 | 0.00 | 12.8 |
| Dischi fermi | 568.1 | 327.6 | 300.9 | 131.17 | 0.00 | 12.8 |

**Limite emerso nella simulazione:** acqua quasi esaurita nei casi: Acciaio riferimento, Volta piana, Focolare profondo 24 cm, Camino diametro 13 cm, Camino alto 1 m, Camino posteriore, Dischi fermi. La disponibilita immediata di acqua nel modello puo sovrastimare la velocita di asciugatura. Le temperature successive non sono una previsione affidabile della pizza reale.

Verifiche numeriche: 13 superate; residuo massimo 9.37e-10 W; differenza di convergenza 0.003495 K.

Il confronto a 30 minuti include il diverso transitorio: una volta refrattaria più fredda a questo istante non implica prestazioni peggiori dopo un preriscaldamento più lungo. Il caso con focolare più profondo mantiene identica potenza di combustione. Il caso a volta piana mantiene identica altezza massima: cambiano area e volume.

La posizione del camino modifica la rete di trasporto tra due zone. Non risolve il campo di velocità, il passaggio di fiamma sotto la volta, il vento o la fuoriuscita di fumo dalla bocca. Il confronto rotante/fermo dipende dal gradiente di esposizione imposto nei parametri.

File: confronto_V3.csv per i dati; study_V3.mat per tutti gli stati, parametri e diagnostiche; confronti_V3.png e geometria_V3.png per i grafici.
