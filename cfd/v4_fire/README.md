# V4: visualizzazione volumetrica e prototipo termico

La vista locale è `http://127.0.0.1:8766/v4-fire/` (server `cfd/serve_viewer.py`).
I volumi provengono dalla run `refined_dx25_t30/c1_v4_two_rotating__front`.
Il colore della fiamma visualizza HRRPUV, non una temperatura o uno spettro ottico.
La fuliggine viene decodificata dai file Smoke3D usando la scala del singolo frame.
Non viene aggiunto movimento procedurale. Il piano termico usa i file slice FDS.
Le geometrie lisce servono da riferimento; il solver usa la geometria voxelizzata.

## Stato della fisica

La vista attuale usa il vecchio caso a propano equivalente con pareti e pizza
a temperatura imposta. Non rappresenta una simulazione validata della quercia.

`build_thermal.py` genera separatamente un prototipo con conduzione transitoria
nei solidi e combustione di gas equivalente al legno. Parte interamente da 25 °C.
Il rilascio di combustibile resta prescritto: non calcola accensione, essiccazione,
pirolisi e consumo dei ciocchi. L'alimento è un materiale omogeneo con conduzione:
evaporazione, rotazione termica e cottura chimica non sono ancora implementate.
Le proprietà dei materiali e gli spessori sono ipotesi, non una distinta costruttiva.
Il rivestimento interno in acciaio è provvisorio; la fotografia non identifica
l'isolante né dimostra che possa rimanere esposto alla fiamma.

Le colonne termiche della volta hanno 1.5 mm di acciaio, 50 mm di isolamento,
1 mm di acciaio. Non modellano ponti termici o conduzione laterale. La superficie
esterna CFD rimane imposta e non è utilizzabile per verificare temperature al tatto.
Le assunzioni precise sono salvate accanto a ogni input in `assumptions.json`.

## Filmato del caso già disponibile

`render_video.py` produce `exports/v4_cfd_fiamma_fumi.mp4` (1280×720)
e `exports/v4_cfd_fiamma_fumi.gif` (960×540), circa 12 secondi.
Usa tutti i 59 campioni volumetrici esportati, da 0 a 29.61274 secondi
simulati. La riproduzione è accelerata di circa 2.5 volte. Non aggiunge
movimenti di fiamma o rotazione delle pizze. Colori e opacità sono una
visualizzazione qualitativa dei campi HRRPUV e fuliggine, ricostruiti
spazialmente con un filtro; non simulano l'aspetto ottico della combustione.
Il camino è sezionato a z=0.70 m per dare spazio alla camera di cottura.
Il vestibolo è disegnato largo 72 cm, profondo 8 cm, alto 16 cm.
Il file `exports/provenienza.json` conserva origine e tempi dei campioni.
Servono NumPy, Pillow e imageio-ffmpeg (quest'ultimo nella cache locale
`~/.cache/forno-video/python`, separata dal progetto).

### Video del nuovo modello termico

`python cfd/v4_fire/render_video.py --thermal` usa esclusivamente
`web/thermal-data` e il CSV delle sonde della nuova run, salvando MP4 e GIF
in `exports/termico/` senza sovrascrivere il video precedente. Mostra tutti
i 93 campioni volumetrici, incluso quello finale a 60 s, in circa 18.6 s.
I tempi del calcolo sono riportati sul video; gli intervalli tra i campioni
sono variabili, quindi l'accelerazione 3.2× è un valore medio.
Le tre temperature sono letture puntuali di superficie (pizze 1 e 2, piano),
interpolate temporalmente dal CSV, non medie della pizza o temperature del gas.
Il video non usa i vecchi valori di temperatura imposta rimasti nei metadati
comuni del caso. La geometria conserva colori illustrativi, non una mappa termica.

## Riproduzione

```text
python cfd/v4_fire/export_volume.py cfd/runs/refined_dx25_t30/c1_v4_two_rotating__front cfd/v4_fire/web/data
python cfd/v4_fire/build_thermal.py cfd/runs/v4_thermal_smoke --seconds 1 --dx .04
```

Formato binario verificato nel sorgente ufficiale FDS 6.11.1 `Source/smvv.f90`.
Composizione elementare del gas dal test ufficiale FDS
`Verification/Pyrolysis/surf_mass_part_char_cart_fuel.fds`; il test non fornisce
parametri calibrati per quercia. Libreria grafica Three.js 0.160.0, licenza MIT.
