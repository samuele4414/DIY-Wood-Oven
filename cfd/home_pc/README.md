# V4 — preriscaldamento e cottura sul PC di casa

Questo pacchetto prepara due simulazioni FDS 6.11.1. **Nessuna nuova simulazione
è stata eseguita sul portatile.** Gli input sono stati generati e verificati
offline; l'accettazione degli input da parte del solver e la convergenza fisica
devono essere verificate sul PC di casa.

## Che cosa cambia

1. **Preriscaldamento:** forno vuoto, tutti gli strati inizialmente a 25 °C,
   durata iniziale 3600 s. La potenza prescritta arriva a 18.75 kW in 60 s.
   Si salvano i profili di temperatura attraverso cordierite, isolamento e acciaio.
2. **Cottura:** pizze inizialmente a 25 °C, durata 120 s; il forno eredita
   i profili termici ottenuti nel preriscaldamento. Il fuoco resta alimentato.
   Questa fase viene preparata solo dopo il completamento della prima e il
   superamento dei criteri di prontezza. `bake.template.fds` è solo un modello
   incompleto da ispezionare: **non eseguirlo direttamente**.

Si conserva la geometria V4, compresi focolare posteriore, volta parabolica,
camino anteriore, piano 79×41 cm e due sedi per pizze Ø30 cm. Non è stata
alterata artificialmente la fiamma per farla arrivare sopra le pizze.

## Avvio su Windows

Installare **Python 3.11 o successivo** e **FDS 6.11.1** dal
[rilascio ufficiale NIST](https://github.com/firemodels/fds/releases/tag/FDS-6.11.1).
Il solver non è incluso nel pacchetto. Usare `fds_openmp.exe` del rilascio:
il runner avvia un solo processo con il numero di thread scelto. Non usa la GPU.

Aprire PowerShell nella cartella principale del pacchetto. Le operazioni di
generazione e controllo usano solo la libreria standard Python.

```powershell
# Mostra i due casi e lo stato, senza eseguire comandi esterni.
python cfd/home_pc/run_home.py --stage all
```

**Solo sul PC destinato al calcolo**, indicando il percorso reale di FDS:

```powershell
python cfd/home_pc/run_home.py --stage all --fds "C:\percorso\FDS6\bin\fds_openmp.exe" --threads 8 --execute
```

`8` è un esempio: scegliere un numero adeguato ai core disponibili. Il comando
esegue preriscaldamento, verifica dei risultati, trasferimento termico e cottura
in sequenza. In alternativa usare `--stage preheat`, controllare il report,
poi usare `--stage bake`. Il comando PowerShell equivalente è:

```powershell
.\cfd\home_pc\RUN_HOME.ps1 -Stage all -Fds "C:\percorso\FDS6\bin\fds_openmp.exe" -Threads 8 -Execute
```

Senza `--execute` o `-Execute` non parte alcun solver. È possibile impostare
`FDS_EXE` al posto di passare il percorso. I file esistenti non vengono cancellati
o sovrascritti per rilanciare una run. Lo stato aggiornato è in
`cfd/home_pc/campaign/<fase>/run_status.json`, l'output in `solver.log` e
`v4_preheat.out` oppure `v4_bake.out`.

## Quando il forno è pronto

Le soglie iniziali, modificabili in `campaign_config.json`, sono **ipotesi di
progetto**: almeno 430 °C nei dieci punti del piano destinati alle pizze,
almeno 450 °C nei quattro punti della volta, differenza sul piano non superiore
a 50 °C e variazione media negli ultimi 120 s entro 3 °C/min.
Non sono temperature assegnate alle superfici: il calcolo deve raggiungerle.
Non equivalgono a una certificazione della cottura.

Se una soglia non è raggiunta, `readiness.json` indica quale criterio fallisce
e la cottura non parte. Un piano troppo freddo può richiedere più tempo; una
forte disuniformità può richiedere una modifica di focolare, flusso o geometria.
Il programma non sostituisce i risultati con temperature calde arbitrarie.

Per cambiare durata, potenza o soglie, modificare il **config sorgente** in
`cfd/home_pc/campaign_config.json`, poi generare una nuova cartella:

```powershell
python cfd/home_pc/pipeline.py prepare --output cfd/home_pc/campaign_02
python cfd/home_pc/run_home.py --campaign cfd/home_pc/campaign_02 --stage all --fds "C:\percorso\fds_openmp.exe" --threads 8 --execute
```

Non modificare il config o gli input dentro una campagna già preparata: gli hash
impediscono di mescolare risultati con impostazioni diverse. I checkpoint FDS
vengono salvati ogni 60 s; il runner non offre ancora ripresa automatica dopo
interruzione. Prima di un eventuale restart manuale verificare i vincoli FDS.

Un'ora **fisica** di riscaldamento può richiedere molte ore di calcolo, anche su
un PC più potente. Gli intervalli di salvataggio più radi nel preriscaldamento
limitano i dati su disco, ma non eliminano i passi temporali del solver.

## Fiamma sopra le pizze e lettura dei risultati

La presenza di una fiamma visibile direttamente sopra tutta la pizza non è,
da sola, una misura della cottura. Vanno confrontati calore radiante da volta
e combustione, convezione dei gas e conduzione dal piano. Questa campagna salva:

- mappe FDS `WALL TEMPERATURE`, `RADIATIVE HEAT FLUX`, `CONVECTIVE HEAT FLUX`
  e `NET HEAT FLUX`;
- cinque punti per pizza: centro, sinistra, destra, davanti e dietro;
- temperatura di superficie, a metà spessore e vicino alla base della pizza;
- temperatura del gas, sezioni di velocità, fumo e rilascio di calore;
- profili completi attraverso i diversi strati del forno.

I `.smv` si aprono con Smokeview, incluso nella distribuzione FDS/SMV. Le mappe
di flusso permettono di individuare punti meno riscaldati; i valori delle sonde
sono puntuali, non medie sull'intera pizza.

## Esportazione dei video dopo il calcolo

```powershell
python -m pip install -r cfd/home_pc/requirements.txt
python cfd/home_pc/export_results.py --stage preheat --video
python cfd/home_pc/export_results.py --stage bake --video
```

Questi comandi elaborano solo risultati completati e non richiamano FDS.
Ogni fase riceve una cartella `visualisation`, un report e una cartella `video`
con MP4 e GIF. Il filmato di preriscaldamento mostra il forno vuoto; quello
di cottura mostra le pizze con le letture delle sonde. Le immagini non sono
una simulazione ottica della fiamma e i colori della geometria non sono una
mappa delle temperature: per queste ultime usare i campi di parete in Smokeview.

## Trasferimento termico e limiti dichiarati

La seconda fase è un **avvio caldo da profili trasferiti**, non un restart
esatto. I profili nodali FDS sono trasferiti per regioni rappresentative:
piano sinistro, piano destro, focolare, volta e camino. La colonna sotto ogni
pizza usa il profilo rilevato nella sua sede; il cibo parte freddo. La transizione
iniziale cibo/piano è regolarizzata in 0.1 mm. Il contatto è perfetto, senza
resistenza di contatto. Le superfici del piano nascoste sotto la pizza diventano
INERT: l'accumulo del substrato è già nella colonna cibo+cordierite+isolamento.

Il gas viene inizializzato dalle temperature regionali misurate, mentre velocità,
specie, turbolenza e campo radiativo vengono ricostruiti dal solver. Un transitorio
iniziale della seconda fase è quindi atteso. Il trasferimento non conserva
ogni variazione spaziale delle pareti e non simula conduzione laterale o ponti
termici. Lo stato esterno della scocca CFD rimane prescritto all'ambiente:
queste run non verificano la temperatura sicura al tatto.

La quercia è ancora rappresentata da **gas equivalente al legno a rilascio
prescritto**, non da ciocchi con pirolisi calibrata. Rivestimento interno da
1.5 mm di acciaio, isolamento da 50 mm e scocca esterna da 1 mm sono ipotesi
provvisorie; l'isolante della fotografia non è stato identificato.

La pizza è uno strato omogeneo di 6 mm, con frazione d'acqua ipotizzata 0.50.
La capacità termica apparente tra 95 e 105 °C include un'energia pari a
`0.50 × 2257 = 1128.5 kJ/kg`. Questo evita di ignorare il calore latente,
ma non calcola acqua persa, vapore rilasciato, ingredienti separati, doratura
o consistenza. Durante raffreddamento la legge apparente è reversibile:
non usarla per dedurre essiccazione irreversibile. Le pizze restano ferme
nella CFD; la rotazione dei piatti non è ancora risolta termicamente.
La temperatura del cibo è una stima termica, non un verdetto «pizza cotta».

## Verifiche e riferimenti

Sono disponibili test offline con dati sintetici chiaramente separati dai
risultati fisici. Controllano trasferimento dei profili, pizza fredda/piano caldo,
conservazione dell'energia latente apparente, blocco del forno non pronto,
provenienza e protezione dalla partenza involontaria del solver.

- [Guida ufficiale e sorgenti FDS 6.11.1](https://github.com/firemodels/fds/tree/FDS-6.11.1):
  User Guide §8.3.4 (`RAMP_T_I`, profondità in metri e °C), §5.6 (restart),
  `Source/init.f90` e `Source/dump.f90` (formato `PROF`).
- [Esempio ufficiale di conduzione](https://github.com/firemodels/fds/blob/FDS-6.11.1/Verification/Heat_Transfer/heat_conduction_kc.fds).
- [NIST: entalpia di vaporizzazione dell'acqua](https://nvlpubs.nist.gov/nistpubs/jres/75A/jresv75An3p213_A1b.pdf).

Non sono stati creati commit né pubblicati file su GitHub.
