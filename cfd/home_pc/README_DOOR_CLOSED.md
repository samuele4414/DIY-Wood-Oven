# V4 — prova di preriscaldamento con porta frontale chiusa

Questo pacchetto contiene **solo gli input** di un nuovo caso FDS. Non contiene
risultati e nessun solver è stato avviato per prepararlo. Conservare separata
la precedente run a bocca aperta: questa usa un CHID diverso e non la sovrascrive.

## Ipotesi e confronto

- Stessa geometria V4, maglia da 25 mm, potenza prescritta di 18,75 kW,
  ambiente a 25 °C e durata di 3600 s della run a bocca aperta.
- Porta anteriore **interamente chiusa**, senza fessura. In FDS occupa le celle
  della bocca discretizzata: `x=0,025…0,775 m`, `y=-0,075…-0,05 m`,
  `z=0…0,15 m`. La canna fumaria rimane aperta.
- La porta è rappresentata provvisoriamente da acciaio 1,5 mm,
  isolante 25 mm e scocca d'acciaio 1 mm. Non è un disegno costruttivo.
- È stata aggiunta una sonda `flue_inward_z_negative`, oltre alle sonde di
  flusso netto e uscente già presenti: serve a verificare se e quanto gas
  entra dalla canna. L'eventuale ingresso non è imposto come condizione.
- Nessuna presa d'aria posteriore è stata inventata. Il modello non riproduce
  il circuito d'aria del Karu. Se la canna non fornisce aria sufficiente,
  questa prova mostrerà proprio il limite del V4 così ipotizzato.
- Il fuoco è ancora un rilascio prescritto equivalente al gas di legna, non
  la pirolisi dei ciocchi. Non usare questa prova per affermare che una vera
  combustione resterebbe stabile con porta chiusa.

La geometria della porta è risolta a gradini di 25 mm. Una verifica successiva
con maglia più fine servirà per il dettaglio di porta, spifferi e prese d'aria.

## Avvio sul PC di casa

Installare Python 3.11+ e FDS 6.11.1 ufficiale. Estrarre lo ZIP in una
cartella nuova e aprire PowerShell nella cartella che contiene `cfd`.

```powershell
python cfd/home_pc/run_home.py --campaign cfd/home_pc/campaign_door_closed --stage preheat
```

Il comando sopra è un controllo **senza calcolo**. Per lanciare la nuova run
solo sul PC di casa, sostituire il percorso con quello reale di FDS:

```powershell
python cfd/home_pc/run_home.py --campaign cfd/home_pc/campaign_door_closed --stage preheat --fds "C:\percorso\FDS6\bin\fds_openmp.exe" --threads 8 --execute
```

Il Ryzen 7 3700X ha 8 core fisici: 8 thread è un punto di partenza, non una
garanzia di velocità ottima. L'eseguibile ufficiale `fds_openmp.exe` esegue
il solver sulla CPU. La RTX 4060 non viene usata per il calcolo CFD da questo
pacchetto. Una build sperimentale GPU richiederebbe un solver diverso e una
nuova verifica numerica; non basta aggiungere un'opzione al comando.

Non usare `--stage all` o `--stage bake`: questo pacchetto prepara soltanto
il confronto del preriscaldamento. Non modificare input o config dopo il
lancio. Il runner rifiuta la sovrascrittura dei risultati già presenti.

## Output dopo il completamento

Quando FDS termina regolarmente a 3600 s, gli output restano in
`cfd/home_pc/campaign_door_closed/preheat`. Per report, dati 3D e video:

```powershell
python -m pip install -r cfd/home_pc/requirements.txt
python cfd/home_pc/export_results.py --campaign cfd/home_pc/campaign_door_closed --stage preheat --video
```

Per confrontare le due prove, controllare temperatura minima e differenza
massima del piano, temperatura minima della volta, portata attraverso la
bocca e flussi **netto, uscente ed entrante** nella canna. Non dedurre il
beneficio della porta dalla sola temperatura di una sonda.
