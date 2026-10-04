function g = oven_compact_front_geometry(p,d,c)
%OVEN_COMPACT_FRONT_GEOMETRY Presa alta integrata; SI, solo ingombri nominali.
% Il raccordo puo sovrapporsi in pianta al piano, essendo sulla copertura.
assert(isscalar(c.frontDepth) && isfinite(c.frontDepth) && c.frontDepth>=0 && ...
    isscalar(c.flueY) && isfinite(c.flueY),'oven:compact','Coordinate non valide.');
% Conserva le verifiche del piano/focolare e il precedente come confronto.
g.reference=oven_dimension_geometry(p,d);
g.doorY=-c.frontDepth;
g.flueCenter=[p.geom.width/2 c.flueY];
g.collarY=c.flueY+[-1 1]*d.collarDiameter/2;
g.pipeY=c.flueY+[-1 1]*d.outerPipeDiameter/2;
g.requiredRoofY=g.collarY+[-1 1]*d.edgeMargin;
g.hotDepth=p.geom.frontDepth+p.geom.rearDepth;
g.overallDepth=c.frontDepth+g.hotDepth;
g.doorToFlueAxis=c.flueY-g.doorY;
g.doorToPlateNear=p.geom.plateCenters(:,2)'-p.geom.plateDiameter/2-g.doorY;
g.doorToPlateCenter=p.geom.plateCenters(:,2)'-g.doorY;
g.collarFrontMargin=g.collarY(1)-g.doorY;
g.collarSideMargin=(p.geom.width-d.collarDiameter)/2;
g.flueArea=pi*p.flow.chimneyDiameter^2/4;
assert(g.requiredRoofY(1)>=g.doorY-1e-12 && ...
    g.requiredRoofY(2)<=p.geom.frontDepth && ...
    g.collarSideMargin>=d.edgeMargin-1e-12,'oven:compact', ...
    'Raccordo e margini devono stare sulla copertura, dietro la porta.');
g.internalLintel=false;
g.thermalOrFlowValidated=false;
g.flags={'Variante geometrica, nessun nuovo risultato termico o di tiraggio.', ...
    'Raccordo sulla copertura: proiezione sovrapposta al piano, nessun foro nel pavimento.', ...
    'Unico vano comunicante fra porta e camera; nessuna chiusura interna a y=0.', ...
    'Adattatore sulla volta, raccolta fumi e aria a porta chiusa da progettare.', ...
    'Margini nominali geometrici, non distanze termiche o spessori costruttivi.'};
end
