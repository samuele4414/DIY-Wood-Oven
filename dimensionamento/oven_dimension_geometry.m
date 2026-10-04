function g = oven_dimension_geometry(p,d)
%OVEN_DIMENSION_GEOMETRY Cappa esterna e ingombri; quote SI interne nominali.
% La cappa davanti alla bocca non aggiunge area al piano di cottura V3.
positive=[d.hoodDepth d.hoodWidth d.collarDiameter d.outerPipeDiameter ...
 d.woodLength d.woodThickness d.peelWidth];
nonnegative=[d.edgeMargin d.woodRowGap d.woodFrontClearance ...
 d.woodRearClearance d.woodSideClearance d.peelSideClearance];
assert(isreal(positive) && all(isfinite(positive)) && all(positive>0) && ...
 isreal(nonnegative) && all(isfinite(nonnegative)) && all(nonnegative>=0), ...
 'oven:dimensions','Ingombri finiti positivi e margini non negativi richiesti.');
assert(isscalar(d.desiredRows) && isfinite(d.desiredRows) && ...
 d.desiredRows>=1 && d.desiredRows==floor(d.desiredRows), ...
 'oven:dimensions','Il numero di file di legna deve essere intero positivo.');
assert(d.outerPipeDiameter>=p.flow.chimneyDiameter && ...
 d.collarDiameter>=d.outerPipeDiameter,'oven:dimensions', ...
 'Diametro esterno >= diametro fumi e flangia >= diametro esterno richiesti.');
assert(d.hoodWidth>=p.geom.mouthWidth,'oven:dimensions', ...
 'La cappa deve coprire la larghezza della bocca.');
g.core=oven_geometry(p);
g.hoodDepth=d.hoodDepth;
g.hoodWidth=d.hoodWidth;
g.hotDepth=p.geom.frontDepth+p.geom.rearDepth;
g.overallDepth=d.hoodDepth+g.hotDepth;
g.mouthY=0;
g.entranceY=-d.hoodDepth;
g.doorSeatY=g.entranceY; % porta esterna: camera e cappa restano comunicanti
g.flueCenter=[p.geom.width/2 -d.hoodDepth/2];
g.doorToFlueAxis=g.flueCenter(2)-g.doorSeatY;
% Rettangolo della cappa centrato rispetto alla camera calda.
g.hoodX=[(p.geom.width-d.hoodWidth)/2 (p.geom.width+d.hoodWidth)/2];
g.collarMargins=[(d.hoodWidth-d.collarDiameter)/2*[1 1] ...
 (d.hoodDepth-d.collarDiameter)/2*[1 1]]; % sinistra destra fronte retro
g.flueMargins=[(d.hoodWidth-p.flow.chimneyDiameter)/2*[1 1] ...
 (d.hoodDepth-p.flow.chimneyDiameter)/2*[1 1]];
assert(all(g.collarMargins>=d.edgeMargin-1e-12),'oven:dimensions', ...
 'Flangia camino e margini non contenuti nella cappa.');
g.frontedgeToPlateNear=d.hoodDepth+p.geom.plateCenters(:,2)'-p.geom.plateDiameter/2;
g.frontedgeToPlateCenter=d.hoodDepth+p.geom.plateCenters(:,2)';
g.fireboxArea=g.core.rearArea;
g.fireboxVolume=g.core.volume(2);
% Pala diritta lungo ciascun asse disco, bocca centrata su x=width/2.
halfTool=d.peelWidth/2+d.peelSideClearance;
g.requiredMouthWidth=2*max(abs(p.geom.plateCenters(:,1)-p.geom.width/2)+halfTool);
g.straightPeelAccess=p.geom.mouthWidth>=g.requiredMouthWidth-1e-12;
g.woodMinRearDepth=d.woodFrontClearance+d.woodRearClearance + ...
 d.desiredRows*d.woodThickness+(d.desiredRows-1)*d.woodRowGap;
available=p.geom.rearDepth-d.woodFrontClearance-d.woodRearClearance;
depthRows=max(0,floor((available+d.woodRowGap+1e-12)/(d.woodThickness+d.woodRowGap)));
g.woodRows=zeros(0,4);
for row=1:depthRows
 y1=d.woodFrontClearance+(row-1)*(d.woodThickness+d.woodRowGap);
 y2=y1+d.woodThickness;
 rowWidths=p.geom.width+(p.geom.rearWidth-p.geom.width)*[y1 y2]/p.geom.rearDepth;
 if min(rowWidths)+1e-12<d.woodLength+2*d.woodSideClearance, break; end
 g.woodRows(end+1,:)=[(p.geom.width-d.woodLength)/2 ...
  (p.geom.width+d.woodLength)/2 p.geom.frontDepth+[y1 y2]];
end
g.maxWoodRows=size(g.woodRows,1);
g.desiredRowsFit=g.maxWoodRows>=d.desiredRows;
g.longitudinalLogFits=available>=d.woodLength-1e-12 && ...
 min(p.geom.width,p.geom.rearWidth)>=d.woodThickness+2*d.woodSideClearance;
g.hoodThermallyModelled=false;
g.flags={'Ingombri nominali interni: pareti, isolamento, supporti e tolleranze da aggiungere.', ...
 'File di legna: verifica di ingombro, non verifica di potenza, carico o combustione.', ...
 'Cappa e coordinate camino non risolte termicamente: cattura fumi non predetta.', ...
 'Porta sul fronte esterno a y=-profondita cappa; passaggio camera-cappa a y=0 aperto.', ...
 'Funzionamento a porta chiusa non simulato; aria di combustione dedicata da dimensionare.', ...
 'Pala non allineabile diritta non significa impossibilita di ingresso angolato.'};
end
