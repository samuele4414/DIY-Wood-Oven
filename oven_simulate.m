function r = oven_simulate(p)
%OVEN_SIMULATE Preriscaldamento, due pizze, rimozione e recupero a fuoco acceso.
if nargin==0, p=oven_defaults(); end
g = oven_geometry(p);
simulationValues = [p.sim.warmupSeconds p.sim.bakeSeconds p.sim.recoverySeconds ...
 p.sim.maxStep p.sim.outputStep p.sim.relTol p.sim.absTol];
assert(all(isfinite(simulationValues)) && p.sim.warmupSeconds>=0 && ...
 p.sim.bakeSeconds>=60 && p.sim.recoverySeconds>0 && p.sim.maxStep>0 && ...
 p.sim.outputStep>0 && p.sim.relTol>0 && p.sim.absTol>0, ...
 'oven:simulation','Tempi non validi; cottura almeno 60 s, tolleranze positive.');
opts = odeset('RelTol',p.sim.relTol,'AbsTol',p.sim.absTol,'MaxStep',p.sim.maxStep, ...
 'NonNegative',g.idx.water(:));
times = [0 p.sim.warmupSeconds p.sim.warmupSeconds+p.sim.bakeSeconds ...
 p.sim.warmupSeconds+p.sim.bakeSeconds+p.sim.recoverySeconds];
r.t=[]; r.y=[]; r.load=[]; y0=g.y0;
for phase=1:3
 if times(phase+1)==times(phase), continue; end
 loaded = phase==2;
 grid = unique([times(phase):p.sim.outputStep:times(phase+1), times(phase+1), ...
  times(phase)+(phase==2)*60]);
 grid = grid(grid>=times(phase) & grid<=times(phase+1));
 [tt,yy] = ode15s(@(t,y)oven_rhs(t,y,p,g,loaded),grid,y0,opts);
 y0 = yy(end,:)';
 if ~isempty(r.t), tt=tt(2:end); yy=yy(2:end,:); end
 r.t=[r.t;tt]; r.y=[r.y;yy]; r.load=[r.load;repmat(loaded,numel(tt),1)];
end
r.p=p; r.g=g; r.labels=g.labels;
for k=1:numel(r.t)
 [~,d] = oven_rhs(r.t(k),r.y(k,:)',p,g,r.load(k));
 if k==1
  fields=fieldnames(d);
  for f=1:numel(fields), r.diagnostics.(fields{f})=zeros(numel(r.t),1); end
 end
 for f=1:numel(fields), r.diagnostics.(fields{f})(k)=d.(fields{f}); end
end
r.metrics.atLoad = snapshot(p.sim.warmupSeconds);
r.metrics.at60 = snapshot(p.sim.warmupSeconds+60);
r.metrics.atRemoval = snapshot(times(3));
r.metrics.at90 = snapshot(p.sim.warmupSeconds+min(90,p.sim.bakeSeconds));
r.metrics.at90.available = p.sim.bakeSeconds>=90;
if ~r.metrics.at90.available
 unavailableFields=fieldnames(r.metrics.at90);
 for k=1:numel(unavailableFields)
  f=unavailableFields{k};
  if ~strcmp(f,'available'), r.metrics.at90.(f)=nan(size(r.metrics.at90.(f))); end
 end
end
r.metrics.afterRecovery = snapshot(times(end));
r.metrics.maxEnergyResidualW = max(abs(r.diagnostics.energyResidual));
r.metrics.minimumWaterKg = min(r.y(:,g.idx.water(:)),[],'all');
r.metrics.maximumPlateBi = max(r.diagnostics.plateBi);
r.metrics.maximumRoofBi = max(r.diagnostics.roofBi);
r.metrics.storedEnergyChangeJ = (r.y(end,:)-r.y(1,:))*g.C;
r.metrics.netEnergyQuadratureJ = trapz(r.t,r.diagnostics.fuelPower- ...
 r.diagnostics.lossPower-r.diagnostics.evapPower);
r.metrics.energyQuadratureErrorJ = r.metrics.storedEnergyChangeJ-r.metrics.netEnergyQuadratureJ;
r.metrics.finalHeatingRateKMin = (r.metrics.afterRecovery.plateMeanC-r.metrics.atRemoval.plateMeanC)*60/p.sim.recoverySeconds;
r.flags = {'Modello preliminare non calibrato: non certifica dimensioni, tiraggio o cottura.', ...
 'Coefficiente spaziale imposto: rotazione non ricava il campo termico dalla geometria.', ...
 'Combustione imposta, senza limite ossigeno, cinetica, vento o cattura fumo.', ...
 'Materiali e isolamento provvisori; densita cordierite 2600 kg/m3 ereditata dalla bozza.', ...
 'Pizza a capacita costante: ebollizione regolarizzata e acqua condivisa base/superficie per settore.', ...
 'Evaporazione limitata dal calore entrante; nessun trasporto umidita, crosta o criterio di pizza cotta.'};
if max(r.metrics.maximumPlateBi,r.metrics.maximumRoofBi)>.1
 r.flags{end+1}='Bi > 0.1: due strati termici inclusi, ma risoluzione nello spessore da verificare.';
end
if max(r.y(:,[g.idx.top(:);g.idx.base(:)]),[],'all')>473.15
 r.flags{end+1}='Pizza oltre 200 C: essiccamento/crosta/degradazione non rappresentati.';
end
if p.pizza.waterFraction>0 && any(r.metrics.atRemoval.waterKg<.01*p.pizza.mass*p.pizza.waterFraction)
 r.flags{end+1}='Acqua quasi esaurita nel modello: tempo di essiccamento non validato senza trasporto di umidita.';
end
 function s=snapshot(tq)
  yy=interp1(r.t,r.y,tq,'linear');
  s.time=tq;
  s.gasC=yy(g.idx.gas)-273.15;
  s.shellC=yy(g.idx.shell)-273.15;
  s.fixedC=yy(g.idx.fixed)-273.15;
  s.plateMeanC=mean(reshape(yy(g.idx.plate(:)),p.geom.sectors,2),1)-273.15;
  s.plateBottomMeanC=mean(reshape(yy(g.idx.plateBottom(:)),p.geom.sectors,2),1)-273.15;
  s.baseMeanC=mean(reshape(yy(g.idx.base(:)),p.geom.sectors,2),1)-273.15;
  tops=reshape(yy(g.idx.top(:)),p.geom.sectors,2);
  s.topMeanC=mean(tops,1)-273.15;
  s.topSpreadK=max(tops,[],1)-min(tops,[],1);
  plates=reshape(yy(g.idx.plate(:)),p.geom.sectors,2);
  s.plateSpreadK=max(plates,[],1)-min(plates,[],1);
  s.waterKg=sum(reshape(yy(g.idx.water(:)),p.geom.sectors,2),1);
 end
end
