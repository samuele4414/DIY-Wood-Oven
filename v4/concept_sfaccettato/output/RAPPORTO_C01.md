# C01 — studio d'ingombro del forno inox sfaccettato

**Stato: non esecutivo.** Nessuna CFD, misura fisica o verifica strutturale nuova.
Unità geometriche: mm. Origine e assi sono quelli di `v4/quote_v4.json`.

## Requisiti confermati

Forno domestico da esterno, appoggio fisso, due pizze Ø300, cottura nominale
60–90 s a forno pronto. Preriscaldamento desiderato 45–60 min; primo obiettivo
di verifica entro 60 min. Questi sono obiettivi, non prestazioni dimostrate.
Riferimento estetico: `design-concepts/14-inox-sfaccettato.png`.

## Baseline geometrica proposta

- Camera V4: piano 790 × 410, dischi Ø320 ai centri (210;205) e (580;205).
- Focolare posteriore trapezoidale, profondità 250; avancorpo interno 80.
- Bocca candidata 720 × 160; botola posteriore 300 × 140.
- Volta interna parabolica: imposta 190, colmo 280. Il suo profilo è esteso
  all'avancorpo SOLO come ipotesi di ingombro; il raccordo reale resta aperto.
- Pietra piano/dischi 20; fondo focolare 30. Sono due ipotesi distinte.
- Acciaio caldo 1,5; lana di roccia 75; montaggio/dilatazioni riservati 10;
  rivestimento esterno 1. Prodotti e leghe non selezionati.
- Isolante inferiore 50, carrier riservato 1,5, vano meccanico netto 120,
  fondo 1,5 e piedini riservati 25. Nessuna verifica di portanza del pannello.
- Scocca a falde trasversali 12° e testate 30°, spalle sfaccettate.

**Ingombro proposto: 965 × 915 ×
617 mm**, altezza del corpo inclusi piedini,
senza camino. Il render molto basso non dimostra disponibilità di questo spazio.

Con canna candidata H1000 dal collare: altezza sul piano d'appoggio
1717; con H1500: 2217.
Non sono altezze di canna approvate. Asse mantenuto (395;45), ANTERIORE:
il prompt del render colloca il camino dietro, ma qui non modifichiamo il
percorso fumi V4 per inseguire un'immagine. Una diversa posizione richiede
un confronto separato di captazione e distribuzione termica.

## Verifica geometrica delle falde

Ogni piano esterno delimita un semispazio di contenimento `n·p ≤ d`, con `|n|=1`.
Si calcola analiticamente il massimo `n·p` sulla camera con volta parabolica,
poi si aggiungono 87.5 mm NORMALI al piano.
Questo evita di confondere lo spessore normale con un semplice incremento
verticale del tetto. I piani inclinati rispettano il pacchetto nominale;
rimangono 85 mm dopo sottrazione
delle due pelli, dei quali 75 per isolamento e 10 di riserva.

**Non è una verifica dell'isolamento reale:** bocca, botola, collare,
giunti, supporti, ponti termici e dilatazioni devono ancora essere progettati.
I pannelli sono superfici/riserve, non solidi di lamiera pronti da piegare.

## Ingombri alternativi

| Isolante | Vano netto | Larghezza | Profondità | Corpo+piedini | Riserve azionamenti |
|---:|---:|---:|---:|---:|---|
| 50 | 80 | 915 | 865 | 551.5 | NO |
| 50 | 120 | 915 | 865 | 591.5 | sì, solo riserva |
| 50 | 160 | 915 | 865 | 631.5 | sì, solo riserva |
| 75 | 80 | 965 | 915 | 577 | NO |
| 75 | 120 | 965 | 915 | 617 | sì, solo riserva |
| 75 | 160 | 965 | 915 | 657 | sì, solo riserva |
| 100 | 80 | 1015 | 965 | 602.6 | NO |
| 100 | 120 | 1015 | 965 | 642.6 | sì, solo riserva |
| 100 | 160 | 1015 | 965 | 682.6 | sì, solo riserva |

Le scatole azionamenti 140 × 140 × 100 non sono motori selezionati.
Servono 10 mm sopra e sotto: lo scenario con vano 80 fallisce questa riserva.
Il vano 120 non prova manutenzione, raffreddamento o montabilità di componenti reali.

## Criticità emerse

1. Altezza e profondità superiori all'impressione del render.
2. Dalla pelle esterna ai centri dei dischi: 372.5;
   dal piano porta interno erano 285. Serve prova della pala nel tunnel aggiunto.
3. Pala ipotizzata 340: solo 5 mm per lato nelle
   posizioni allineate. Esclusi telaio, tolleranze e manovra inclinata.
4. Gioco radiale dischi 1: semplice ipotesi V4, NON tolleranza di taglio.
5. Collettore viola: riserva x70…720, y−60…120, z180…215. NON un condotto
   dimensionato; può modificare irraggiamento e captazione. Raccordo da definire.
6. Sotto i dischi: riserva per un carrier isolato. Meccanica e appoggi
   devono essere definiti prima di attribuire conduzione e ponti termici.
7. Presa d'aria non dimensionata. 60/90 cm² restano scenari della rete,
   non tagli geometrici approvati. Non usare una porta chiusa senza aria progettata.
8. Massa della SOLA pietra: circa 29.4 kg,
   con densità ipotizzata 2600 kg/m³.
   Ogni disco: 4.2 kg. Telaio, pelli, isolanti, motori,
   camino e accessori sono esclusi: non è la massa del forno.

## Stato delle simulazioni preesistenti

La campagna CFD da un'ora usa pietra 30 e isolante generico 50; non questa C01.
Il suo `readiness.json` riporta `ready=false`: piano minimo circa 289 °C,
escursione circa 76 °C, volta minima circa 405 °C. La cottura successiva è
stata avviata in deroga alle soglie. La scocca esterna non è validata al tatto.
Il confronto di spessori 10/20/30 e isolanti 50/75/100 NON è stato simulato qui.

## Controlli effettuati

18 test automatici geometrici/numerici superati durante la generazione:
posizioni V4, supporto della parabola contro campionamento denso, distanze
normali, contenimento, sezioni, bocca aperta, ingombri alternativi,
camino completo, volumi riservati e massa indicativa delle pietre.
Sono controlli del generatore, NON prove del forno reale.

## Consegne

- `index.html`: visualizzatore 3D offline, varianti e viste tecniche.
- `pianta.svg`, `sezione_trasversale.svg`, `sezione_longitudinale.svg`.
- `assieme.svg`: modello geometrico con camino completo.
- `scheda_stampa.html`: scheda stampabile; PDF con lo script opzionale.
- `ingombri_C01.dxf`: riferimento nominale 2D in mm, NON profili di taglio.
- `assieme_C01.obj` + `.mtl`: superfici/riserve 3D in mm, non solidi manifatturabili.
- `confronto_ingombri.csv`, `verifica_geometrica.json`, `provenienza.json`.
- `PIANO_VERIFICHE.md`: sequenza e criteri da definire prima del prototipo.

Prossimo gate: circuito aria/collettore, prodotti reali e architettura dei dischi.
Solo dopo aggiornare i modelli e qualificare un prototipo strumentato.
