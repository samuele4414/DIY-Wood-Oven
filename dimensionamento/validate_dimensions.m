function report = validate_dimensions()
%VALIDATE_DIMENSIONS Verifiche geometriche ed evento ODE, non validazione fisica.
[p,d]=oven_dimension_defaults(); g=oven_dimension_geometry(p,d); checks={};
assert(abs(g.overallDepth-.91)<1e-12 && abs(g.hotDepth-.66)<1e-12);
assert(max(abs(g.frontedgeToPlateNear-.295))<1e-12 && ...
 max(abs(g.frontedgeToPlateCenter-.455))<1e-12);
assert(abs(g.core.eaveHeight-.19)<1e-12 && g.mouthY==0 && g.entranceY==-.25);
assert(g.doorSeatY==g.entranceY && abs(g.doorToFlueAxis-.125)<1e-12);
assert(g.doorSeatY<g.flueCenter(2)-d.collarDiameter/2 && ...
 g.flueCenter(2)+d.collarDiameter/2<g.mouthY);
checks{end+1}='Ingombro 91 cm, camera 66 cm, distanze ingresso e imposta 19 cm';
assert(abs(g.core.fixedArea+2*g.core.plateArea+g.core.gapArea-.79*.41)<1e-12);
assert(~g.hoodThermallyModelled);
checks{end+1}='La cappa non duplica l area termica del piano 79x41 cm';
assert(g.maxWoodRows==2 && g.desiredRowsFit && abs(g.woodMinRearDepth-.24)<1e-12);
assert(~g.longitudinalLogFits);
short=p; short.geom.rearDepth=.14; gs=oven_dimension_geometry(short,d);
assert(gs.maxWoodRows==1 && ~gs.desiredRowsFit);
checks{end+1}='Legna trasversale 25x7 cm: 2 file in 25 cm, 1 fila in 14 cm';
taper=p; taper.geom.rearWidth=.28; taper.geom.hatchWidth=.20;
td=d; td.woodLength=.49;
gt=oven_dimension_geometry(taper,td);
assert(gt.maxWoodRows==1 && ~gt.desiredRowsFit);
checks{end+1}='Verifica della larghezza trapezio lungo tutta la fila di legna';
assert(all(g.collarMargins>=d.edgeMargin-1e-12) && abs(g.flueCenter(2)+.125)<1e-12);
bad=d; bad.hoodDepth=.22;
mustReject(@()oven_dimension_geometry(p,bad),'oven:dimensions');
bad=d; bad.hoodDepth=-.25;
mustReject(@()oven_dimension_geometry(p,bad),'oven:dimensions');
bad=d; bad.hoodDepth=NaN;
mustReject(@()oven_dimension_geometry(p,bad),'oven:dimensions');
checks{end+1}='Cappa contiene flangia e margini; 22 cm, negativo e NaN rifiutati';
assert(g.straightPeelAccess && abs(g.requiredMouthWidth-.72)<1e-12);
narrow=p; narrow.geom.mouthWidth=.60; gn=oven_dimension_geometry(narrow,d);
assert(~gn.straightPeelAccess);
checks{end+1}='Pala 34 cm: accesso diritto 72 cm; bocca 60 cm richiede manovra';
noFuel=p; noFuel.fuel.kgH=0;
h=oven_preheat_target(noFuel,450,2);
assert(~h.reached && isnan(h.timeSeconds) && abs(h.endTimeSeconds-2)<1e-12);
assert(max(abs(h.y(end,:)-h.g.y0'))<1e-10);
checks{end+1}='Target non raggiunto senza combustibile: NaN tempo e equilibrio';
h=oven_preheat_target(p,p.ambient-273.15,2);
assert(h.reached && h.timeSeconds==0 && isscalar(h.t));
checks{end+1}='Target gia raggiunto allo stato iniziale';
h=oven_preheat_target(p,p.ambient-273.15+.05,30);
assert(h.reached && h.timeSeconds>0 && h.timeSeconds<30 && ...
 abs(h.endPlateC-h.targetPlateC)<1e-5);
checks{end+1}='Arresto evento ODE sulla temperatura media superiore richiesta';
report.passed=true; report.checks=checks;
fprintf('Dimensionamento: %d verifiche superate.\n',numel(checks));
end

function mustReject(action,identifier)
rejected=false;
try
 action();
catch e
 rejected=strcmp(e.identifier,identifier);
end
assert(rejected,'oven:test','Parametro non valido non rifiutato come previsto.');
end
