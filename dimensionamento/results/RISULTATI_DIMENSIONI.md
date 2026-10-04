# Dimensionamento preliminare — risultati

**Candidato geometrico, non progetto esecutivo:** profondita totale 91 cm = 25 cappa + 41 piano + 25 focolare. Piano 79 x 41 cm, dischi Ø32 cm.

Raccordo di ingombro Ø19 cm dentro cappa 25 cm, con 3.0 cm davanti/dietro. Distanza ingresso esterno–bordo dischi 29.5 cm; ingresso–centri 45.5 cm.

**Porta sul fronte esterno:** battuta coincidente con l'ingresso a y = -25.0 cm. Dall'esterno verso l'interno: porta, cappa con presa del camino, camera con due pizze, focolare. L'asse del camino e 12.5 cm verso l'interno rispetto alla porta. Il passaggio a y = 0 resta permanentemente aperto fra camera e cappa, senza porta interna. Apertura della porta e passaggio della camera: 72 x 16 cm.

Legna lunga 25 cm, spessore ipotizzato 7 cm: 2 file trasversali geometricamente compatibili. Profondita minima per le 2 file richieste 24 cm, nei margini ipotizzati.

Il preriscaldamento termina alla media superiore dischi di 450 C. Caso base: combustibile 3.5 kg/h, potenza immessa 10.2 kW; due pizze di 250 g e Ø30 cm per 90 s. La soglia e un riferimento di confronto, non un criterio di cottura.

| Caso | Raggiunge 450 C entro 120 min | Preriscaldamento min | Volta anteriore al carico C | Calo dischi nei 90 s K |
|---|---|---:|---:|---:|
| candidato_25cm | no, finale 442.1 C | — | — | — |
| focolare_14cm | si | 61.7 | 402.1 | 144.8 |
| focolare_20cm | si | 110.1 | 406.5 | 145.1 |
| focolare_30cm | no, finale 435.2 C | — | — | — |
| volta_25cm | no, finale 443.8 C | — | — | — |
| volta_30cm | no, finale 440.9 C | — | — | — |
| bocca_alta_14cm | no, finale 449.4 C | — | — | — |
| bocca_larga_60cm | si | 96.5 | 414.3 | 145.1 |
| camino_diametro_15cm | no, finale 372.7 C | — | — | — |
| camino_altezza_50cm | si | 39.4 | 417.8 | 143.5 |
| volta_refrattaria | no, finale 374.6 C | — | — | — |
| legna_4_5kg_h | si | 34.1 | 416.5 | 142.8 |
| legna_4_5kg_h_pietra_20mm | si | 58.6 | 421.8 | 100.4 |

Le due prove finali usano 4.5 kg/h. Il caso con pietra 20 mm si confronta con il precedente a 4.5 kg/h e 10 mm: lo spessore modifica piano fisso, dischi e focolare.

**Limite quantitativo emerso:** in 6 dei 6 casi caricati il modello porta l'acqua residua sotto 1 g per pizza. L'asciugatura troppo rapida segnala la necessita di un modello di trasporto interno dell'umidita e di dati di prova. Il calo di temperatura della pietra non va assunto come valore atteso sul prototipo.

Le differenze sono previsioni del modello non calibrato. Non costituiscono una graduatoria di configurazioni ottimali. Il maggiore volume posteriore non aumenta automaticamente la potenza di combustione: la portata di legna resta imposta.

**Cappa:** verificata in pianta; assente come volume dai bilanci termici V3. I risultati di tiraggio non verificano aspirazione, diluizione o fuoriuscita di fumo.

**Porta chiusa:** il collegamento geometrico fra camera e camino rimane aperto, ma il funzionamento a porta chiusa non e simulato. La V3 conserva ingresso d'aria imposto e bocca aperta; l'alimentazione dell'aria di combustione a porta chiusa va dimensionata separatamente. La geometria non dimostra il funzionamento con chiusura ermetica.

Ridurre diametro o altezza del camino per trattenere piu calore non dimostra un tiraggio adeguato: i requisiti di raccolta e scarico fumi restano da verificare.

**Pizza:** asciugatura e contatto sono ancora semplificati; leggere il calo termico come risposta al carico del modello, non come prova di cottura reale.

Verifiche dimensionali eseguite: vedere struttura validation in study.mat.

Quote e motivazioni: [LEGGIMI](../LEGGIMI.md). Dati completi: summary.csv e study.mat.
