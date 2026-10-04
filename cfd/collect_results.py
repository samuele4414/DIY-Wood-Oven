"""Reduce actual FDS results and build the versioned interactive comparison.

No data are invented for absent, failed or unfinished solver runs.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import shutil

from check_geometry import nominal_check
from postprocess import summarize_run
from run_study import ROOT, load_cases


def compact(value):
    if isinstance(value, float):
        return round(value, 5) if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k:compact(v) for k,v in value.items()}
    if isinstance(value, list):
        return [compact(v) for v in value]
    return value


def collect(family, visualization=None):
    results = {}
    provenance = {}
    run_root = ROOT/'runs'/family
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    for casepath in sorted(run_root.glob('*/case.json')):
        case = json.loads(casepath.read_text(encoding='utf-8'))
        run_dir = casepath.parent
        metadata = json.loads((run_dir/f"{case['id']}_metadata.json").read_text(encoding='utf-8'))
        summary = summarize_run(case, run_dir, metadata)
        status_path = run_dir/'run_status.json'
        status = json.loads(status_path.read_text()) if status_path.exists() else {}
        summary['cell_size_m'] = metadata['cell_size_m']
        summary['resolved_geometry'] = metadata['resolved']
        summary['elapsed_wall_s'] = status.get('elapsed_wall_s')
        # Do not publish changing partial fields as a completed comparison.
        results[case['id']] = compact(summary)
        provenance[case['id']] = {
            'input_sha256':status.get('input_sha256'),
            'solver_version':'FDS 6.11.1',
            'run_family':family,
            'status':summary['status'],
            'actual_time_s':summary['time_s'],
        }
        if summary['status'] == 'completed':
            raw = out/'measurements'/case['id']
            raw.mkdir(parents=True,exist_ok=True)
            for suffix in ('devc.csv','hrr.csv'):
                source = run_dir/f"{case['id']}_{suffix}"
                if source.exists():
                    shutil.copy2(source,raw/source.name)
    payload = {'study_id':'oven_cfd_01','cases':load_cases(),'results':results}
    encoded = json.dumps(compact(payload),ensure_ascii=False,allow_nan=False,separators=(',',':'))
    (out/'comparison_CFD01.json').write_text(encoded+'\n',encoding='utf-8')
    (out/'provenance_CFD01.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    template = (ROOT/'viewer.template.html').read_text(encoding='utf-8')
    target = '<script type="application/json" id="ov-data">__OVEN_DATA__</script>'
    if template.count(target) != 1:
        raise ValueError('Missing or duplicate JSON data element')
    fragment = template.replace(target, '<script type="application/json" id="ov-data">'
                                + encoded.replace('</','<\\/') + '</script>')
    destination = Path(visualization) if visualization else out/'oven-cfd-01.html'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(fragment,encoding='utf-8')
    if destination.stat().st_size >= 1_000_000:
        raise ValueError('Inline visualization exceeds 1 MB')
    write_report(results,family)
    print(json.dumps({'results':len(results),'completed':sum(r['status']=='completed' for r in results.values()),
                      'visualization':str(destination),'bytes':destination.stat().st_size}))


def write_report(results,family):
    lines = ['# Studio CFD 01 — risultati effettivi', '',
             f'Famiglia di calcolo: `{family}`. Solo i casi indicati come completati hanno raggiunto il tempo richiesto con arresto normale del solutore.', '',
             '**Studio esplorativo, non validato sperimentalmente né indipendente dalla maglia.** Le temperature riportate sono del gas. La pizza è una superficie a 100 °C imposti: il calcolo non ne prevede la temperatura né i secondi di cottura.', '',
             '## Geometrie', '',
             '| Caso | Pizze | Ingombro interno cm | Zona legna m² | Minimo spazio fra pizze/piatti cm |',
             '|---|---:|---|---:|---:|']
    cases = load_cases()
    for i,c in enumerate(cases,1):
        g = nominal_check(c)
        dims = ' × '.join(f'{v:g}' for v in g['nominal_internal_bbox_cm'])
        lines.append(f"| C{i} | {g['pizza_count']} | {dims} | {g['fire_zone_area_m2']:.3f} | {g['minimum_inter_item_gap_cm']:.1f} |")
    lines += ['', '## Output CFD', '',
              'Flussi in g/s. La bocca può avere contemporaneamente ingresso e uscita: vengono mantenuti distinti. Il flusso totale di aria/gas non equivale alla percentuale di cattura del fumo.', '',
              '| Caso | Aspirazione | Stato | Tempo s | HRR medio kW | Bocca ingresso | Bocca uscita | Canna uscita | Gas sopra pizze °C |',
              '|---|---|---|---:|---:|---:|---:|---:|---|']
    for i,c in enumerate(cases,1):
        for f,label in [('front','Anteriore'),('central','Centrale')]:
            r = results.get(c['id']+'__'+f,{})
            m = r.get('metrics',{})
            def number(key,factor=1):
                v = m.get(key)
                return '—' if v is None else f'{v*factor:.2f}'
            temps = m.get('pizza_gas_temperature_C',[])
            if not isinstance(temps,list):
                temps = []
            texttemps = ' / '.join('—' if v is None else f'{v:.0f}' for v in temps) or '—'
            t = r.get('time_s')
            lines.append(f"| C{i} | {label} | {r.get('status','non eseguito')} | {t if t is not None else '—'} | {number('hrr_kw_mean')} | {number('mouth_in_kg_s',1000)} | {number('mouth_out_kg_s',1000)} | {number('flue_out_kg_s',1000)} | {texttemps} |")
    lines += ['', '## Interpretazione e limiti', '',
              '- Le sezioni del visualizzatore sono medie dei file binari FDS realmente prodotti. La finestra effettiva e la quota compaiono nel risultato JSON. Non sono colori assegnati al disegno per simulare un risultato.',
              '- La volta, il piano e le pareti della canna hanno temperatura prescritta; l’energia scambiata con queste superfici non è limitata dalla sola potenza del bruciatore. Si confrontano condizioni di esercizio imposte, non rendimento energetico o riscaldamento da freddo.',
              '- I piatti circolari sono fermi nel calcolo del gas. La rotazione nella vista 3D è meccanica e illustrativa; non costituisce una simulazione della cottura di una pizza in movimento.',
              '- La maglia grossolana altera aree, curvature e altezza effettiva delle aperture; i metadati documentano le sezioni risolte. La maglia deve essere raffinata prima di dimensionare il camino.',
              '- I valori di gas sopra le pizze sono sonde puntuali richieste a quota 100 mm dal piano, campionate nelle celle FDS corrispondenti: non sono temperature della pizza né flussi termici completi. Non bastano per scegliere la migliore uniformità di cottura.',
              '- La durata breve e le fluttuazioni LES non dimostrano convergenza statistica. Le differenze tra finestre temporali successive sono disponibili nel JSON.',
              '- Stessa quota di uscita camino, 1280 mm dal piano. Bocca aperta, assenza di vento, fuoco prescritto equivalente a 18,75 kW lordi. Porte e carico della legna non vengono manovrati.',
              '- Per scegliere acciaio isolato/refrattario e temperatura della scocca serve aggiungere conduzione, proprietà dipendenti dalla temperatura e spessori; nessun risultato attuale dimostra che la scocca resti fredda.', '',
              'Il confronto geometrico identifica C2 come variante compatta per tre pizze; la pizza posteriore resta da verificare con la pala. C3 offre tre posizioni in fila con una bocca più larga. Queste sono considerazioni geometriche, non una graduatoria CFD.', '',
              'Metodo e fonti: [CFD_METHOD.md](../docs/CFD_METHOD.md), [manuali ufficiali FDS/Smokeview](https://pages.nist.gov/fds/manuals.html).']
    (ROOT/'results'/'report_CFD01.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--family',default='coarse_dx40_t30')
    p.add_argument('--visualization')
    args = p.parse_args()
    collect(args.family,args.visualization)
