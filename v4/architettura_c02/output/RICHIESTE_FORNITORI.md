# C02 — richieste tecniche per completare la distinta

**Bozze da inviare solo dopo revisione dell'utente.** Nessun fornitore è stato
contattato, nessun prezzo o ordine è stato richiesto automaticamente.

## R1 — ceramica piano, dischi e appoggi

Uso: forno domestico outdoor a legna, due pizze Ø300; dischi Ø320, 20 mm
come candidato, confronti 10/20/30. Piano fisso nominale 790 × 410,
focolare posteriore 30. Temperatura/cicli di progetto ancora da definire,
non sostituibili dal valore di fusione. Richiedere:

- Prodotto e composizione esatti, documentazione alimentare per temperatura,
  contatto e pulizia previsti, condizioni di primo utilizzo.
- Densità, cp(T), lambda(T), dilatazione media/istantanea chiaramente distinta,
  flessione/compressione a caldo, shock e limiti d'uso/raffreddamento.
- Tolleranze di diametro, spessore, planarità e resistenza a carico pala al bordo.
- Appoggio consigliato: superficie di ripartizione, sbalzi massimi, montaggio
  flottante e ritenzione di frammenti. Non proporre incollaggio alla lamiera.
- Supporti ceramici strutturali: carico, area di contatto, creep a temperatura,
  resistenza ai cicli e k(T). La sola lana/pannello isolante non è l'appoggio.

## R2 — inox e isolamento industriale

Shortlist: 310S / 1.4845 vs 253 MA / 1.4835, camera nominale 1,5 mm e campioni 1,5/2/3;
scocca 304 da 1 mm, 316L con ambiente aggressivo; WM970 SW nominale 75 mm;
famiglia PROMASIL come sottofondo 50 mm, grado ancora aperto.

- Confermare forma/spessori disponibili, certificati di colata e proprietà
  reali; idoneità e finitura per uso alimentare dove pertinente.
- Per il metallo: deformazione, cicli/creep, saldabilità, filler e pulizia.
- Per la lana: prodotto/variante e spessore 75 disponibile, rete/filo inox,
  binder, ritiro/assestamento, k(T), faccia calda ammessa, SUIS/SDS e prima cottura.
- Per il pannello: grado preciso, ritiro e k/cp, acqua, resistenza/creep a caldo.
  Nessun dato di famiglia deve essere usato come certificato di portanza.
- Qualificare giunti e contenimento fibre: nessuna fibra esposta a camera,
  aria secondaria o cibo. Nessun attraversamento approvato solo per spessore.

## R3 — moduli di rotazione e controllo

Due moduli indipendenti; ciascuno entro riserva 240 × 180 in pianta, vano 160 netto,
160 non interamente disponibile al motore. Motoriduttore laterale 24 V,
cartuccia portante distinta. Pietra circa 4,18 kg e assieme ipotizzato 7,18 kg
con pizza; spinta pala 40 N, momento al bordo 6,4 Nm: combinazioni da verificare.

- CAD e quote orientamento, fissaggi, cablaggio, giunto, pulegge e tensionamento.
- Velocità uscita candidata 0,3/0,6/1 rpm; uso continuo per sessione da specificare.
- Coppia continua/spunto, rapporto ed efficienza, attrito a bassa velocità,
  backlash, possibilità di disaccoppiamento. Screening 0,75–1,35 Nm NON basta
  a selezionare il motore; serve coppia misurata sporco/caldo.
- Cuscinetti: carico assiale/radiale e momento, layout, gioco/precarico,
  crescita assiale, lubrificante/tenute e limiti individuali di temperatura.
- Temperatura avvolgimenti/involucro, grasso/rulli/anelli, duty, grado IP e
  condensa per uso esterno. Obiettivo aria vano 50 °C non è una misura.
- Protezione contro blocco, limitazione coppia/corrente, arresto accessibile,
  nessun riavvio automatico; PSU e cablaggio progettati da persona competente.
- Modulo estraibile frontale senza sollevare il forno; sequenza a freddo da
  dimostrare prima di promettere manutenzione dall'appoggio fisso.

## R4 — circuito aria e sistema camino

Focolare posteriore, raccolta anteriore; bocca 720 × 160. Confronti aria 60/90/120
cm² netti, camino DN130/DN150, H idraulica 1/1,5 m. Consumo 4,5 kg/h e lambda 2
sono scenari non calibrati, non specifiche operative del prodotto.

- Griglia reale: curva portata/DeltaP, area netta dichiarata, rete anti-insetti
  e anti-pioggia, ritiro/regolazione minima e comportamento sporco.
- Perdite di distributori e braci; partizione aria primaria/secondaria come
  portate, non semplice rapporto di aree; nessun collegamento ai motori.
- Camino: DoP/istruzioni per Italia, codici e classificazione a combustibile/
  temperatura/fuliggine, diametri interni/esterni, giunti/flange/terminali.
- SUPER ICS DN130/25 catalogo esterno 180; 50 su richiesta: confermare CAD e
  dimensione reale, senza estrapolare dal solo spessore dichiarato.
- Supporto DN130 catalogo A238/B306: definire telaio carichi statici e vento;
  collare superiore 260 e base ottagonale 440 sono riserve, non pezzi qualificati.
  Il budget rettangolare 260 × 328 richiede circa 416 tra facce in un ottagono
  con normali facce X/Y e 45°: base 340 scartata. La base 440 sporge 7,5 mm
  davanti alla pelle C01; raccordo e scocca da integrare.
- Temperatura camera/fumi non ancora verificata: T450/T600 richiedono scelta
  della configurazione pertinente. La certificazione del tubo non certifica il forno.
- Raccordo graduale, continuità a porta chiusa, accesso pulizia, dilatazioni e
  tenuta; integrare quote idrauliche incluse altezze utili 955/455 dei moduli.
- Captazione: accensione, regime, apertura frontale, ricarica posteriore e
  vento, con DeltaP, O2/CO nei fumi e CO operatore. Limiti da definire per
  prodotto/installazione con tecnico competente; la sola osservazione non basta.

## Dati per il gate componenti

Per ogni voce registrare `codice`, `documento/revisione`, `CAD`, `temperatura`,
`carico/coppia`, `quote/tolleranze`, `criterio`, `responsabile`, `stato`.
Non segnare una voce «approvata» solo perché il produttore dichiara una
temperatura massima. Prove su sandwich e singolo disco precedono il forno completo.
