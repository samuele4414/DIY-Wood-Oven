"""Compare actual 40/25 mm reference outputs, without claiming convergence."""
from __future__ import annotations
import json
from pathlib import Path
from postprocess import summarize_run
from run_study import ROOT


def read_result(family, caseid):
    folder = ROOT/'runs'/family/caseid
    if not (folder/'case.json').exists():
        return {'status':'not_run'}
    case = json.loads((folder/'case.json').read_text(encoding='utf-8'))
    metadata = json.loads((folder/f'{caseid}_metadata.json').read_text())
    result = summarize_run(case,folder,metadata)
    result['cell_size_m'] = metadata['cell_size_m']
    result['resolved_geometry'] = metadata['resolved']
    return result


def build():
    comparisons = {}
    lines = ['# Sensibilità alla discretizzazione — riferimento V4', '',
             'Confronto a 40 e 25 mm dello stesso riferimento, alle stesse condizioni imposte. Due maglie grossolane non dimostrano indipendenza dalla griglia. Cambiano anche l’approssimazione a gradini del camino, della volta e lo spessore risolto della pizza (una cella): sono tutti contributi dell’errore geometrico/numerico.', '',
             '| Aspirazione | Stato 40 / 25 mm | Canna g/s, 40 / 25 mm | Gas sopra pizze °C, 40 / 25 mm |',
             '|---|---|---|---|']
    for f, label in [('front','Anteriore'),('central','Centrale')]:
        cid = 'c1_v4_two_rotating__'+f
        coarse = read_result('coarse_dx40_t30',cid)
        fine = read_result('refined_dx25_t30',cid)
        comparison = {'coarse':coarse,'finer':fine,'differences':{}}
        if coarse['status'] == fine['status'] == 'completed':
            for name in ('hrr_kw_mean','mouth_out_kg_s','mouth_in_kg_s','flue_out_kg_s',
                         'mouth_soot_out_kg_s','flue_soot_out_kg_s','soot_flue_fraction_of_measured_exits'):
                a,b = coarse['metrics'].get(name),fine['metrics'].get(name)
                if a is not None and b is not None:
                    comparison['differences'][name] = {'coarse':a,'finer':b,'difference':b-a,
                                                       'relative_to_finer':(b-a)/abs(b) if abs(b)>1e-12 else None}
        comparisons[f] = comparison
        def flow(r):
            v = r.get('metrics',{}).get('flue_out_kg_s')
            return '—' if v is None else f'{v*1000:.2f}'
        def temps(r):
            values = r.get('metrics',{}).get('pizza_gas_temperature_C',[])
            return ', '.join('—' if x is None else f'{x:.0f}' for x in values) or '—'
        lines.append(f"| {label} | {coarse['status']} / {fine['status']} | {flow(coarse)} / {flow(fine)} | {temps(coarse)} / {temps(fine)} |")
    lines += ['', 'Le differenze misurate vanno lette insieme alle aree effettive delle aperture e alla variabilità temporale. Una piccola differenza tra queste due maglie non certifica accuratezza; una differenza grande esclude l’uso del solo confronto grossolano per stabilire quote costruttive.', '',
              'Le sonde sono richieste alla stessa quota di 100 mm. La sezione visualizzata segue invece la quota dei nodi effettivi del file FDS, registrata nel JSON. Non confondere la temperatura del gas con quella della pizza.']
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    (out/'mesh_sensitivity_CFD01.json').write_text(json.dumps(comparisons,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
    (out/'mesh_sensitivity_CFD01.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({f:{'coarse':c['coarse']['status'],'finer':c['finer']['status']} for f,c in comparisons.items()}))


if __name__ == '__main__':
    build()
