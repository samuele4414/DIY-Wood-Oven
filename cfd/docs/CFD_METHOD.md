# Metodo CFD preliminare — FDS

Questi casi confrontano percorsi di fiamma e raccolta dei fumi in condizioni di esercizio **prescritte**. Non sono una previsione della cottura, dell'accensione o delle emissioni di un forno a legna.

## Solver e modello

Si usa Fire Dynamics Simulator (FDS), un codice LES per flussi a bassa velocità con enfasi su trasporto di fumo e calore da incendi; Smokeview visualizza i risultati. È una scelta pratica per confrontare bocca aperta, cappa, camino, plume e ricircoli in un volume piccolo.

- [FDS e Smokeview, progetto ufficiale](https://github.com/firemodels/fds)
- [Manuali e versione corrente FDS-SMV](https://pages.nist.gov/fds/manuals.html)
- [Guide tecniche, di verifica e validazione del rilascio 6.11.1](https://github.com/firemodels/fds/releases/tag/FDS-6.11.1)
- [Esempio ufficiale di `SURF HRRPUA`, `REAC` e `OPEN`](https://github.com/firemodels/fds/blob/master/Verification/Controls/device_test.fds)

Non si usa Boussinesq: fra aria ambiente e gas a centinaia di °C la variazione di densità è troppo grande per l'approssimazione lineare. FDS risolve un flusso a bassa velocità a densità variabile. In una fase successiva OpenFOAM `buoyantPimpleFoam` può servire per geometrie mobili o accoppiamenti termici più speciali; anche quel caso deve usare gas ideale/comprimibile, non il solver Boussinesq.

## Condizione di screening

La simulazione parte con superficie interna della volta e delle pareti a 500 °C, piano a 450 °C, pizza a 100 °C e facce esterne a 25 °C. Sono condizioni al contorno fisse, scelte per classificare i percorsi di flusso di un forno già caldo. Non rappresentano isolamento, massa, transitorio di preriscaldamento o temperatura reale della pizza.

La sorgente usa un bruciatore FDS prescritto con rampa di 5 s. Per 4,5 kg/h di legna e PCI 15 MJ/kg la potenza chimica lorda è 18,75 kW; questa è la base di `HRRPUA`. Il caso a 13,1 kW è solo una sensibilità inferiore collegata all'efficienza globale del precedente modello termico. La reazione con propano è un proxy numerico per la stechiometria e il plume: non rende la combustione della legna, la produzione di fumo, la frazione radiativa o le emissioni predittive. La resa di fuliggine e la frazione radiativa sono dichiarate ipotesi.

## Geometria, aperture e uscite

Il generatore voxelizza piano poligonale o circolare, volta a botte/paraboloide, vestibolo, bocca, piastre/pizze e canna circolare. La bocca è un'apertura geometrica verso un volume di aria esterna. Non è un ingresso a velocità prescritta. Anche la sommità della canna comunica con tale volume, i cui limiti distanti sono `OPEN`.

Per mantenere la maglia da 25 mm praticabile sul computer disponibile, la griglia è divisa in due mesh conformi e adiacenti: una inferiore che contiene l'intero forno e l'aria davanti alla bocca, e una superiore ristretta attorno alla canna. L'interfaccia fra le due mesh non è dichiarata `OPEN`; le aperture `OPEN` sono solo sulle superfici esterne. Questo segue l'uso di mesh adiacenti nell'[esempio di verifica FDS](https://github.com/firemodels/fds/blob/master/Verification/Controls/device_test.fds). Ogni cambiamento della divisione richiede un nuovo smoke test: un'interfaccia trattata come apertura esterna interromperebbe il condotto.

Le piastre sono complanari; nel CFD iniziale le pizze sono ostruzioni fisse. La rotazione modifica quale settore è esposto al campo già calcolato e viene trattata nel post-processing; non richiede una griglia mobile per scegliere fra le configurazioni della cappa. Una griglia scorrevole/OpenFOAM sarebbe necessaria solo per studiare la dinamica meccanica dei dischi o ostacoli non assialsimmetrici.

Gli output sono HRR, flusso di massa netto alle sezioni di bocca e canna, temperatura e velocità in sezioni orizzontali/verticali. Alla bocca il verso +Y è entrante: la componente negativa è miscela gassosa che esce verso l'operatore. Alla canna il verso +Z è uscente. Il flusso di miscela non è tutto fumo; i dispositivi della specie SOOT misurano separatamente il trasporto della fuliggine del proxy. I flussi di fuliggine sono confrontabili solo perché tutti i casi usano la stessa resa imposta; non sono emissioni previste della legna. Smokeview è lo strumento per viste tridimensionali dei campi; una visualizzazione CAD delle piastre è distinta da una simulazione CFD.

## Maglia e criteri di validità

Con 18,75 kW il diametro caratteristico dell'incendio è circa 0,20 m. La prima campagna usa 40 mm su tutte le configurazioni e 25 mm sul riferimento V4: la canna da 130 mm ha soltanto circa 3 e 5 celle attraverso il diametro. Questo è uno screening grossolano, non una soluzione indipendente dalla maglia. Un confronto credibile del tiraggio richiede ulteriori maglie da 20 e 15 mm e raffinamento locale di gola/canna verso 10–13 mm. Una coppia di maglie non dimostra convergenza. La durata iniziale è 30 secondi, con medie dei dati effettivi sugli ultimi 10; va aumentata se le statistiche continuano a cambiare. Le sonde del gas sopra le pizze restano a quota richiesta z=0,10 m in tutte le maglie.

Le pareti e la canna sono a gradini voxel: le aree risolte della bocca e del bore, la connettività della canna e la potenza per area effettiva sono scritte nei metadati accanto al caso. Prima di usare una geometria per una decisione occorre verificare che la canna sia connessa e che la sezione risolta non sia stata alterata eccessivamente dalla maglia.

## Limiti e calibrazione richiesta

I risultati confrontano le configurazioni soltanto alle stesse condizioni imposte. Non fissano diametro della canna, altezza, potenza della legna o dimensione della cappa. Nei confronti fra prese a quote diverse si mantiene una stessa quota assoluta di uscita: la lunghezza effettiva del tubo viene quindi registrata nei metadati e può differire. Sono indispensabili prove fisiche successive con temperature di pietra, volta, gas e camino, consumo della legna, tiraggio e osservazione della cattura dei fumi. Il vento è un insieme di casi separato: un risultato in aria ferma non dimostra affidabilità all'aperto.
