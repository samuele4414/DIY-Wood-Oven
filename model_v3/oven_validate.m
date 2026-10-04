function report = oven_validate()
%OVEN_VALIDATE Verifiche numeriche, non validazione fisica sperimentale.
p=oven_defaults(); g=oven_geometry(p); checks={};
assert(abs(g.fixedArea+2*g.plateArea+g.gapArea-g.frontArea)<1e-12);
assert(numel(g.labels)==numel(g.C) && numel(g.y0)==numel(g.C));
checks{end+1}='Aree senza sovrapposizioni e dimensioni degli stati';
bad=p; bad.geom.plateCenters(2,:)=bad.geom.plateCenters(1,:);
rejected=false;
try
 oven_geometry(bad);
catch e
 rejected=strcmp(e.identifier,'oven:geometry');
end
assert(rejected); checks{end+1}='Geometria sovrapposta rifiutata';
peq=p; peq.fuel.kgH=0;
[dy,d]=oven_rhs(0,g.y0,peq,g,true);
assert(max(abs(dy))<1e-11 && abs(d.energyResidual)<1e-10);
checks{end+1}='Equilibrio ambiente senza sorgenti';
y=g.y0; thermal=g.C>0;
y(thermal)=350+mod((1:nnz(thermal))'*73,600);
worst=0;
for material={'steel','refractory'}
 pp=p; pp.roof.material=material{1}; gg=oven_geometry(pp);
 for position={'front','rear'}
  pp.flow.chimneyPosition=position{1};
  for loaded=[false true]
   [~,d]=oven_rhs(17,y,pp,gg,loaded);
   worst=max(worst,abs(d.energyResidual));
   assert(abs(d.energyResidual)<1e-7);
  end
 end
end
checks{end+1}='Conservazione energia: due materiali, due camini, con/senza pizze';
% Isolare l'irraggiamento pizza: la perdita della volta deve includerlo.
pr=p; pr.fuel.kgH=0; pr.flow.mixingKgS=0; pr.heat.gasH=0;
pr.heat.pizzaH=0; pr.heat.contactH=0; pr.heat.pizzaInternalH=0;
yr=g.y0; yr(g.idx.shell)=800;
[a,~]=oven_rhs(0,yr,pr,g,false); [b,~]=oven_rhs(0,yr,pr,g,true);
delta=g.C.*(b-a);
assert(sum(delta(g.idx.top(:)))>0 && abs(sum(delta))<1e-7);
assert(abs(sum(delta(g.idx.shell))+sum(delta(g.idx.plate(:)))+sum(delta(g.idx.top(:))))<1e-7);
% La pizza sostituisce l'area di disco visibile: non si duplica irraggiamento.
checks{end+1}='Pizza e schermatura disco: irraggiamento reciproco e senza duplicazioni';
pd=p; pd.fuel.kgH=0; yd=g.y0; yd(g.idx.gas)=250;
[~,d]=oven_rhs(0,yd,pd,g,false); assert(d.massFlow==0 && d.draftPa==0);
checks{end+1}='Nessuna radice negativa quando gas piu freddo dell ambiente';
yd=g.y0; yd(g.idx.top(:))=500; yd(g.idx.water(:))=0;
[dy,~]=oven_rhs(0,yd,p,g,true); assert(all(dy(g.idx.water(:))==0));
checks{end+1}='Evaporazione nulla quando acqua esaurita';
% Forno caldo e pizza bagnata al limite di ebollizione: nessun ulteriore
% riscaldamento sensibile; tutto il calore netto entrante diventa latente.
wet=g.y0; wet(thermal)=800;
pizzaNodes=[g.idx.base(:);g.idx.top(:)];
boilingCap=p.pizza.evaporationTemperature+p.pizza.evaporationTransitionK;
wet(pizzaNodes)=boilingCap;
[wetDy,wetD]=oven_rhs(0,wet,p,g,true);
dry=wet; dry(g.idx.water(:))=0;
[dryDy,dryD]=oven_rhs(0,dry,p,g,true);
assert(max(abs(wetDy(pizzaNodes)))<1e-10 && all(dryDy(pizzaNodes)>0));
assert(wetD.evapPower>0 && dryD.evapPower==0 && all(wetDy(g.idx.water(:))<0));
assert(abs(wetD.evapPower+p.pizza.latentHeat*sum(wetDy(g.idx.water(:))))<1e-8);
assert(abs(sum(g.C.*(dryDy-wetDy))-wetD.evapPower)<1e-7 && abs(wetD.energyResidual)<1e-7);
checks{end+1}='Ebollizione umida base e superficie limitata dal calore, conservazione latente';
cold=wet; cold(pizzaNodes)=p.pizza.evaporationTemperature-1;
[coldDy,coldD]=oven_rhs(0,cold,p,g,true);
assert(coldD.evapPower==0 && all(coldDy(g.idx.water(:))==0));
checks{end+1}='Nessuna evaporazione sotto la soglia di ebollizione nel modello';
hotOptions=odeset('RelTol',1e-6,'AbsTol',1e-8,'MaxStep',.5,'NonNegative',g.idx.water(:));
[~,hotY]=ode15s(@(t,state)oven_rhs(t,state,p,g,true),0:1:60,wet,hotOptions);
assert(all(isfinite(hotY),'all') && min(hotY(:,g.idx.water(:)),[],'all')>=-1e-10);
for pizza=1:2
 for sector=1:p.geom.sectors
  isWet=hotY(:,g.idx.water(sector,pizza))>=p.pizza.waterTransitionKg/p.geom.sectors;
  assert(all(hotY(isWet,[g.idx.base(sector,pizza) g.idx.top(sector,pizza)])<=boilingCap+.01,'all'));
 end
end
checks{end+1}='Integrazione calda 60 s: acqua non negativa e vincolo bagnato rispettato';
% In campo uniforme la velocita non deve cambiare alcuna derivata.
pu=p; pu.heat.rearExposureAmplitude=0; pu.rotation.rpm=[0 0];
[a,~]=oven_rhs(13,y,pu,g,true); pu.rotation.rpm=[8 8];
[b,~]=oven_rhs(13,y,pu,g,true); assert(max(abs(a-b))<1e-12);
checks{end+1}='Rotazione priva di effetto artificiale nel campo uniforme';
ps=p; ps.sim.warmupSeconds=15; ps.sim.recoverySeconds=10; ps.sim.outputStep=5;
r1=oven_simulate(ps);
assert(all(isfinite(r1.y),'all') && r1.metrics.minimumWaterKg>=-1e-10);
ps.sim.relTol=ps.sim.relTol/10; ps.sim.absTol=ps.sim.absTol/10; ps.sim.maxStep=1;
r2=oven_simulate(ps);
err=max(abs(r1.y(end,thermal)-r2.y(end,thermal)));
assert(err<.1,'oven:convergence','Differenza convergenza oltre 0.1 K.');
checks{end+1}='Integrazione finita, acqua non negativa, convergenza breve <0.1 K';
ps.sim.bakeSeconds=60;
short=oven_simulate(ps);
assert(~short.metrics.at90.available && all(isnan(short.metrics.at90.topMeanC)) && ...
 short.metrics.atRemoval.time==ps.sim.warmupSeconds+60);
checks{end+1}='Cottura 60 s: rimozione corretta e nessuna falsa misura a 90 s';
report.passed=true; report.checks=checks; report.maxEnergyResidualW=worst;
report.convergenceMaxK=err;
fprintf('V3: %d verifiche numeriche superate; residuo %.3g W; convergenza %.3g K.\n', ...
 numel(checks),worst,err);
end
