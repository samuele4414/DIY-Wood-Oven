# C03 — piano e registro del banco a freddo

**Piano futuro, non autorizzazione a costruire o accendere. Nessuna prova
eseguita.** Il modulo del CAD è incompleto: prima del banco occorrono
progetto dei carichi/accoppiamenti, revisione meccanica/elettrica e criteri
di prova scritti. Il banco è un solo asse, protetto, non il forno acceso.

## Gate prima di azionare

- Identificare componenti reali, seriali/revisioni, fori/calettamenti, sedi, grasso/tenute, precarico e telaio. Carico portato dalla cartuccia, non dal motore o dal pannello.
- Pesi/disco trattenuti anche in caso di rottura; schermo e carter fissati, parti mobili inaccessibili, banco stabile e supporto del modulo estratto predisposto.
- Alimentazione/quadro protetti progettati da tecnico; arresto accessibile verificato, nessun riavvio automatico. Segnale ALM open-loop non è un rilevatore di impuntamento affidabile.
- Definire carichi massimi, margini su coppia/temperature, limiti di eccentricità/oscillazione e durata prima di iniziare; gli110,5N/6,4Nm/1,346Nm C03 sono scenari, non carichi di collaudo approvati.
- Strumenti con calibrazione/incertezza e acquisizione sincronizzata: encoder indipendente sul disco, trasduttore coppia, corrente appropriata PWM/fase, temperatura aria/corpo/riduttore/cartucce, comparatori e forza cinghia.
- Coppia di mantenimento/limite corrente non equivalgono a limitazione sicura della coppia; definire risposta a bloccaggio e perdita alimentazione.

## Sequenza proposta

| ID | Prova futura | Dato da acquisire / condizione d'uscita |
|---|---|---|
| BF01 | Montaggio manuale disalimentato | Catena di carico, ritegni e accesso utensili dimostrati; nessun contatto |
| BF02 | Geometria e giochi | Diametri, planarità, eccentricità, oscillazione; budget tolleranze completo |
| BF03 | Precarico cinghia | Tensione misurata e forza radiale coerenti con fornitore; non applicare F0=40 come ricetta |
| BF04 | Velocità e regolarità | Encoder disco a0,3/0,6/1rpm; passi persi, pulsazioni, avviamenti e correnti |
| BF05 | Coppia pulito/sporco | Coppia di spunto/marcia misurata, variazione detriti; protezione contro ingresso nei componenti |
| BF06 | Portanza/momento | Solo carichi approvati dal dimensionamento; deformazioni e reazioni, ritenzione pietra |
| BF07 | Temperatura in marcia/riposo | Aria, motore/riduttore, cartuccia e driver/quadro fino a stabilizzazione concordata; corrente/derating verificati |
| BF08 | Manutenzione | Sostenere disco, disaccoppiare, abbassare e sfilare; tempo, utensili, cablaggi e appoggio senza sollevare forno |
| BF09 | Guasti controllati | Con dispositivo protetto: arresto, perdita alimentazione, rilevazione blocco/perdita movimento; nessun riavvio |
| BF10 | Cicli/riesame | Durata e ripetizioni concordate, usura/precarico pulizia; riesame risultati e anomalie |

Il registro CSV contiene solo queste righe pianificate, statoNON_ESEGUITA,
e misure vuote. Compilarle solo con dati reali: non copiare previsioni
nelle colonne di misura. Conservare grezzi, unità, incertezza, revisione,
operatori, criteri/esiti e fotografie come allegati separati.

## Manutenzione: condizioni particolari

La corsa orizzontale è circa465,5, mentre300 è la riserva davanti al forno.
Disco/carrier devono essere sostenuti PRIMA di scollegare l'albero. Guide,
disconnessione, sostegno abbassamento12, fermi anticaduta e schermo solidale
al cassetto sono ancora da progettare. Il passaggio280 × 144 lascia solo1mm
per lato verticale oltre riserva3: nessun gate superato senza mockup con
componenti veri, tolleranze, cavi e utensili. Un montante o uno schermo
fisso nel percorso potrebbe impedire l'estrazione.

## Dallo sviluppo a freddo al caldo

Non trasferire un risultato del banco freddo a uso nel forno. Per il
campione caldo seguire il riesame C02, con interfaccia calda vera,
carichi/temperature dei componenti, sonde e picco dopo spegnimento.
Aria/fumi, captazione/CO, superfici accessibili e durata sono verifiche
distinte. Nessuna prova a combustione pianificata da questo documento.
