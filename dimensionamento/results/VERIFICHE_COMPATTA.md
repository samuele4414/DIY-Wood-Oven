# Verifiche della variante compatta

**Esito:** compatibilita nominale in pianta confermata; appoggio sulla volta e ingombri tridimensionali ancora da dettagliare. Camino e captazione a porta aperta non approvati come progetto costruttivo. La rete di pressione individua condizioni favorevoli e criticita sotto ipotesi esplicite.

## Geometria

Piano 79 x 41 cm, retro 25 cm, avancorpo 8 cm: profondita nominale 74 cm. Porta-bordo dischi 12.5 cm, porta-centri 28.5 cm. Raccordo Ø19 dietro la porta con 3 cm nominali, solo margine geometrico.

Con gioco radiale ipotizzato 1 mm: ponte fisso tra i tagli 48.0 mm, ponte anteriore 44.0 mm. Non verificata resistenza della cordierite o dilatazione. La volta e 20.5 cm sopra il piano ai lati della bocca alta 16 cm. La curvatura produce 5.2 mm di dislivello fra centro e bordo laterale del raccordo: serve un adattatore sagomato. Non e una flangia piana direttamente posata sulla volta.

**Sovrapposizione ammessa:** collare e presa sulla volta possono stare sopra le pizze in pianta. Il criterio e la distanza verticale del collettore dal volume utile, non la separazione dei loro contorni dall'alto. La formula della volta descrive il tratto sopra il piano; il profilo dell'avancorpo di 8 cm e il sostegno anteriore del raccordo non sono ancora dettagliati.

Pala ipotizzata 34 cm: passaggio 72 cm lascia solo 5 mm per lato nel caso allineato a ciascun disco. Sono esclusi telaio, tolleranze, variazioni utensile e verifica della manovra. Il focolare contiene due file di ciocchi 25 x 7 cm nelle distanze nominali gia definite: non dimostra autonomia o potenza del fuoco.

## Ipotesi riproducibili

Legna 4.5 kg/h, umidita tal quale 20%, aria teorica 6.271 kg/kg secco. Il riferimento lambda=2 e solo una scelta di confronto. Temperatura gas camera 500 C uniforme, media camino 250 C, ambiente 25 C. Non sono temperature calcolate dal modello termico. Tubo Ø13 cm, altezza verticale sopra il tetto 1.0 m, K locale complessivo 4.0, fattore Darcy 0.03, Cd presa e bocca 0.65. Coefficienti ipotizzati, senza misura di raccordo, griglia, letto di braci o terminale. Presa posteriore bassa: 60 cm² LIBERI NETTI, centro a 3 cm sopra il piano.

La rete risolve la pressione della camera e conserva la massa di aria piu combustibile gasificato (ceneri escluse). Con porta aperta integra separatamente entrata e uscita lungo l'altezza; non impone tutta la bocca come ingresso. Vento positivo ostacola lo scarico. La massa di legna resta imposta anche se manca aria: lambda basso segnala un'ipotesi di combustione incompatibile, non una combustione simulata.

## Risultati

| Scenario | lambda presa posteriore | Uscita bocca kg/h | Margine a lambda=2 Pa |
|---|---:|---:|---:|
| Base chiusa | 1.87 | 0.0 | -0.97 |
| Presa 30 cm2 | 1.13 | 0.0 | -14.07 |
| Presa 90 cm2 | 2.27 | 0.0 | 1.46 |
| Camino 0.5 m | 1.48 | 0.0 | -3.37 |
| Camino 1.5 m | 2.18 | 0.0 | 1.44 |
| Diametro 15 cm | 2.08 | 0.0 | 0.52 |
| Fumi 150 C | 1.70 | 0.0 | -1.89 |
| Fumi 100 C | 1.54 | 0.0 | -2.66 |
| Perdite K=8 | 1.55 | 0.0 | -4.16 |
| Vento avverso 3 Pa | 1.37 | 0.0 | -3.97 |
| Vento avverso 6 Pa | 0.58 | 0.0 | -6.97 |
| Legna 3.5 kg/h | 2.42 | 0.0 | 2.09 |
| Porta aperta | 0.59 | 60.8 | NaN |
| Aperta, gas 300 C | 0.54 | 56.8 | NaN |
| Aperta, camino 1.5 m | 0.61 | 56.9 | NaN |
| Chiusa H1.5 A90 | 2.66 | 0.0 | 3.87 |
| H1.5 A90 T150 K8 vento3 | 1.43 | 0.0 | -3.40 |

Margine positivo: pressione sufficiente alla portata richiesta nelle sole ipotesi del caso. Margine negativo: il riferimento lambda=2 non e raggiunto. Non sono un giudizio di sicurezza o una prova di buona combustione. NaN: riferimento non applicato alla porta aperta.

**Base a porta chiusa:** lambda 1.87; per lambda=2 servono circa 68 cm² netti nel caso base. Il valore cambia con temperatura, perdite e vento. Una griglia al 60% di area libera richiede un'area lorda pari a quella netta divisa per 0.60, prima di considerare le sue perdite aggiuntive. Una misura come 20 x 3 cm e 60 cm² lordi, non necessariamente netti.

**Porta aperta:** nel caso base il piano neutro e a 8.3 cm, sotto il bordo alto a 16 cm. La rete prevede flusso uscente in alto (60.8 kg/h di gas, non massa di fumo o CO). Variando Cd bocca 0.50/0.65/0.80, l'uscita calcolata e 42.7/60.8/79.0 kg/h. E un segnale che il semplice foro nel tetto non supera questa verifica semplificata. La portata reale non e validata: mancano stratificazione, inerzia del getto, deflettore, raccolta tridimensionale e vento variabile. Lambda totale include aria dalla porta che puo non raggiungere il fuoco; in inversione include anche aria entrata dal camino. Non prova adeguata alimentazione della legna.

**Controllo energetico condizionato:** si assume che tutti i gas lascino il volume camera alla sua temperatura uniforme; il raffreddamento nel tubo avviene dopo. La temperatura media assegnata alla canna serve a calcolarne la densita e non e la temperatura all'uscita dalla camera. L'estrazione sensibile nel caso aperto e 18.7 kW, contro 13.1 kW di potenza rilasciata ipotizzata, prima di radiazione e altre perdite. Se la prima supera la seconda, le temperature imposte non sono sostenibili a regime: il caso rappresenta soltanto uno stato caldo transitorio alimentato anche dall'accumulo. Non e stato risolto il raffreddamento nel tempo.

## Conseguenze per la prossima geometria

- Mantenere 8 cm come avanzamento candidato: le sole pressioni non ne verificano l'effetto.
- Prevedere una presa posteriore regolabile con area libera misurabile; verificare 60 e 90 cm² come scenari, insieme al percorso attraverso/sopra le braci.
- Confrontare altezza camino 1 e 1.5 m; l'altezza superiore non risolve da sola la bocca aperta. I confronti Ø15 sono solo idraulici: tubo, raccordo e ingombri vanno riselezionati.
- Disegnare un collettore/deflettore alto anteriore con transizione graduale verso il tubo, poi verificare l'uscita durante apertura della porta. Nessuna sezione minima definitiva e dedotta qui.
- Provare accensione, regime, ricarica posteriore e apertura frontale con misura di temperature fumi, pressione differenziale, consumo/umidita legna e osservazione dei fumi; O2/CO nei fumi servono a valutare la combustione. Ripetere sotto vento.

## Equazioni e fonti

`rho = p/(R T)`; `P(z) = P0 + g(rho_a-rho_c)z`; `DeltaP_camino = P0 + g(rho_a-rho_c)z_tetto + gH(rho_a-rho_f) - P_vento`; `Ktot = Klocali + f_D H/D`; `m = A sqrt(2 rho DeltaP / Ktot)`.

Aria secca teorica: `[(8/3)C + 8H - O] / xO2`, con C/H/O frazioni massiche su base secca. Massa secca = massa tal quale x (1-umidita).

- [USDA, Wood as a Fuel](https://www.srs.fs.usda.gov/pubs/gtr/gtr_so024.pdf): composizione media del legno e bilancio stechiometrico; l'eccesso d'aria riportato nel manuale non prescrive quello di questo forno.
- [NIST CONTAM 3.2](https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1887.pdf): reti di pressione, orifizi, aperture con flussi in entrambe le direzioni, sezione Doorways.
- [NISTIR 89-4035](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir89-4035.pdf): tiraggio idrostatico e perdite nei condotti.

**Validazione numerica:** 8 controlli superati; massimo residuo di massa 4.94e-14 kg/s. Questo verifica il calcolo, non la fedelta al forno reale.

Riproduzione: `s = run_draft_checks();`. Parametri in `oven_draft_defaults.m`; risultati completi in verifiche_fumi.csv e verifiche_fumi.mat, grafico verifiche_fumi.png.
