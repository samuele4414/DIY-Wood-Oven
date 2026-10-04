"""Check nominal packing independently of FDS voxelisation.

Reports diameters and actual clearances, rather than inferring capacity from
floor area. Does not certify peel manoeuvrability or log loading access.
"""
import json
import math
from pathlib import Path
from run_study import ROOT, load_cases
from fds_writer import inside_plan


def segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def polygon_area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points, points[1:]+points[:1])))/2


def nominal_check(c):
    plan = c['plan']
    r = c['disc_diameter']/2 if c['rotating'] else c['pizza_diameter']/2
    wall_gaps = []
    fire_gaps = []
    for center in c['pizza_centers']:
        if not inside_plan(c, *center):
            raise ValueError(f"Pizza centre outside floor: {c['id']}")
        if plan['kind'] == 'circle':
            cx, cy = plan['center']
            wall = min(plan['radius']-math.hypot(center[0]-cx, center[1]-cy), center[1])
        else:
            pts = plan['points']
            wall = min(segment_distance(center, a, b) for a,b in zip(pts, pts[1:]+pts[:1]))
        wall_gaps.append(wall-r)
        pts = c['fire_polygon']
        fire_gaps.append(min(segment_distance(center, a,b) for a,b in zip(pts,pts[1:]+pts[:1]))-r)
    centers = c['pizza_centers']
    pair_gaps = [math.dist(a,b)-2*r for i,a in enumerate(centers) for b in centers[i+1:]]
    if min(wall_gaps+fire_gaps+pair_gaps) < -1e-6:
        raise ValueError(f"Nominal collision: {c['id']}")
    if plan['kind'] == 'circle':
        radius, cy = plan['radius'], plan['center'][1]
        removed = radius*radius*math.acos(cy/radius)-cy*math.sqrt(radius*radius-cy*cy)
        area = math.pi*radius*radius-removed
    else:
        area = polygon_area(plan['points'])
    return {'case_id':c['id'], 'pizza_count':len(centers),
            'nominal_internal_bbox_cm':[round(100*c['width'],2),round(100*(c['depth']+c['front_extension']),2)],
            'floor_area_m2':round(area,5), 'fire_zone_area_m2':round(polygon_area(c['fire_polygon']),5),
            'occupied_diameter_cm':round(200*r,2),
            'minimum_wall_gap_cm':round(100*min(wall_gaps),2),
            'minimum_fire_zone_gap_cm':round(100*min(fire_gaps),2),
            'minimum_inter_item_gap_cm':round(100*min(pair_gaps),2),
            'notes':c['notes']}


if __name__ == '__main__':
    results = [nominal_check(c) for c in load_cases()]
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    (out/'geometry_checks.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(results,indent=2,ensure_ascii=False))
