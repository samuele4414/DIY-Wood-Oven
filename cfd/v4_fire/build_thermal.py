"""V4 conjugate 1-D solid / 3-D gas prototype. No calibrated oak pyrolysis."""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_study import load_cases, variant
from fds_writer import write_case


def build(destination, seconds=60., dx=.025):
    case = variant(load_cases()[0], 'front')
    case['id'] = 'v4_thermal_woodgas'
    case['label'] = case['id']
    case['thermal_model'] = 'Cold-start 1D solid conduction; prescribed generic wood-gas release'
    meta = write_case(case, destination, cell_size=dx, duration=seconds)
    path = destination / (case['id']+'.fds')
    text = path.read_text()
    materials = """
! Assumed preliminary properties. Not identified from a photograph.
&MATL ID='STEEL', DENSITY=7900., CONDUCTIVITY=16., SPECIFIC_HEAT=0.5 /
&MATL ID='INSULATION', DENSITY=128., CONDUCTIVITY=0.12, SPECIFIC_HEAT=1. /
&MATL ID='CORDIERITE', DENSITY=2600., CONDUCTIVITY=2.5, SPECIFIC_HEAT=0.9 /
&MATL ID='BOARD', DENSITY=250., CONDUCTIVITY=0.09, SPECIFIC_HEAT=1. /
&MATL ID='FOOD', DENSITY=650., CONDUCTIVITY=0.4, SPECIFIC_HEAT=3. /
"""
    # Generic elemental composition follows the FDS wood example, not oak kinetics.
    text = re.sub(r"&REAC[^/]+/", "&REAC ID='WOODGAS_PROXY', FUEL='WOOD', C=3.4, H=6.2, O=2.5, HEAT_OF_COMBUSTION=15000., SOOT_YIELD=0.015, RADIATIVE_FRACTION=0.35 /"+materials, text, count=1)
    surfaces = {
        'WALL_HOT': "MATL_ID(1,1)='STEEL', MATL_ID(2,1)='INSULATION', MATL_ID(3,1)='STEEL', THICKNESS=0.0015,0.05,0.001",
        'FLOOR_HOT': "MATL_ID(1,1)='CORDIERITE', MATL_ID(2,1)='BOARD', THICKNESS=0.03,0.05",
        'CHIMNEY_INNER': "MATL_ID='STEEL', THICKNESS=0.001",
        'PIZZA_PREHEATED': "MATL_ID(1,1)='FOOD', MATL_ID(2,1)='CORDIERITE', MATL_ID(3,1)='BOARD', THICKNESS=0.006,0.03,0.05",
    }
    for key, spec in surfaces.items():
        replacement = f"&SURF ID='{key}', {spec}, TMP_INNER=25., TMP_GAS_BACK=25., HEAT_TRANSFER_COEFFICIENT_BACK=8., EMISSIVITY=0.9 /"
        text = re.sub(r"&SURF ID='"+key+r"'[^/]+/", replacement, text)
    # Food/floor column only on the upper face: no duplicated floor layers on pizza sides.
    text = text.replace("SURF_ID='PIZZA_PREHEATED'", "SURF_IDS='PIZZA_PREHEATED','FOOD_EDGE','INERT'")
    text = text.replace('&TAIL /', "&SURF ID='FOOD_EDGE', MATL_ID='FOOD', THICKNESS=0.006, BACKING='INSULATED', TMP_INNER=25. /\n&TAIL /")
    text = re.sub(r'&DUMP[^/]+/', '&DUMP DT_DEVC=0.5, DT_SLCF=0.5, DT_HRR=0.5, DT_BNDF=1., DT_SMOKE3D=0.25, DT_RESTART=5. /', text)
    devices = ["&BNDF QUANTITY='WALL TEMPERATURE' /", "&BNDF QUANTITY='NET HEAT FLUX' /"]
    for n,(x,y) in enumerate(case['pizza_centers'],1):
        for quantity,suffix in [('WALL TEMPERATURE','surface'),('NET HEAT FLUX','flux')]:
            devices.append(f"&DEVC ID='pizza_{n}_{suffix}', XYZ={x},{y},{dx}, IOR=3, QUANTITY='{quantity}' /")
    devices.append("&DEVC ID='floor_surface', XYZ=0.395,0.20,0., IOR=3, QUANTITY='WALL TEMPERATURE' /")
    text = text.replace('&TAIL /', '\n'.join(devices)+'\n&TAIL /')
    text = text.replace('Preheated prescribed-HRR oven screening:', 'Cold start solid/gas thermal prototype:')
    path.write_text(text, encoding='ascii')
    assumptions = {
        'user_fuel': 'Quercia ben stagionata',
        'fuel_model': 'Generic wood-gas elemental surrogate; prescribed 18.75 kW ramp, not log pyrolysis',
        'moisture': 'Not measured; 15 MJ/kg effective LHV is an assumption, no explicit drying',
        'roof_layers_m': [0.0015,0.05,0.001],
        'roof_layers': ['provisional inner steel liner','provisional AES-type insulation','outer steel'],
        'initial_temperature_C':25,
        'food': '6 mm homogeneous thermal surrogate; no evaporation, browning or rotation',
        'conduction': 'Independent 1D columns normal to surfaces; no lateral thermal bridges',
        'outside': 'Back of thermal columns exchanges with 25 C ambient, h=8 W/m2/K; exterior CFD skin remains prescribed',
        'purpose': 'Cold-start coupling check, not pizza bake time or safe exterior temperature validation',
        'source': 'https://github.com/firemodels/fds/blob/FDS-6.11.1/Verification/Pyrolysis/surf_mass_part_char_cart_fuel.fds',
    }
    (destination/'assumptions.json').write_text(json.dumps(assumptions,indent=2),encoding='utf-8')
    (destination/'case.json').write_text(json.dumps(case,indent=2),encoding='utf-8')
    return path


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);p.add_argument('--seconds',type=float,default=60);p.add_argument('--dx',type=float,default=.025)
    a=p.parse_args();print(build(a.destination,a.seconds,a.dx))

