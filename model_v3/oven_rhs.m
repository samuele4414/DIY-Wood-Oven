function [dy,d] = oven_rhs(t,y,p,g,loaded)
%OVEN_RHS Bilanci a coppie; tutte le temperature in K, acqua in kg.
% Le masse termiche sono costanti. Evaporazione limitata dal calore entrante:
% base e superficie condividono acqua disponibile nello stesso settore.
% Ebollizione regolarizzata, senza trasporto umidita'/cottura validato.
i = g.idx; N = p.geom.sectors; Ta = p.ambient;
q = zeros(g.nStates,1); dy = q;
fuel = p.fuel.kgH/3600*p.fuel.lhv*p.fuel.efficiency;
w = p.fuel.radiantWeights;
assert(all(w>=0) && sum(w)>0 && p.fuel.radiantFraction>=0 && ...
 p.fuel.radiantFraction<=1,'oven:parameters','Partizione combustione non valida.');
w = w/sum(w);
q(i.gas(2)) = fuel*(1-p.fuel.radiantFraction);
q([i.shell i.hearth]) = fuel*p.fuel.radiantFraction*w(:);
% Tiraggio senza pressione del vento, attrito e ingresso mediante K globali.
if strcmpi(p.flow.chimneyPosition,'front'), outlet=1; inlet=2;
else, outlet=2; inlet=1; end
rhoA = p.flow.pressure/(p.flow.gasConstant*Ta);
rhoFlue = p.flow.pressure/(p.flow.gasConstant*max(y(i.gas(outlet)),1));
draft = max(0,p.flow.gravity*p.flow.chimneyHeight*(rhoA-rhoFlue));
resistance = p.flow.chimneyLoss/(rhoFlue*g.chimneyArea^2) + ...
 p.flow.inletLoss/(rhoA*g.inletArea^2);
mdot = sqrt(2*draft/resistance);
cp = p.flow.cp;
% Rete seriale: aria ambiente -> zona inlet -> zona outlet -> camino.
% Per camino frontale l'aria alla zona posteriore rappresenta il sottocorrente;
% nessuna predizione CFD di cattura fumo o distribuzione locale del tiraggio.
q(i.gas(inlet)) = q(i.gas(inlet))+mdot*cp*(Ta-y(i.gas(inlet)));
q(i.gas(outlet)) = q(i.gas(outlet))+mdot*cp*(y(i.gas(inlet))-y(i.gas(outlet)));
flueLoss = mdot*cp*(y(i.gas(outlet))-Ta);
exchange(i.gas(2),i.gas(1),p.flow.mixingKgS*cp*(y(i.gas(2))-y(i.gas(1))));
for zone=1:2
 areas = [g.frontShellArea g.rearShellArea];
 exchange(i.gas(zone),i.shell(zone),p.heat.gasH*areas(zone)*(y(i.gas(zone))-y(i.shell(zone))));
end
exchange(i.shell(2),i.shell(1),p.heat.shellLink*(y(i.shell(2))-y(i.shell(1))));
surface(i.fixed,g.fixedArea,0,p.floor.emissivity,p.heat.gasH);
surface(i.hearth,g.rearArea,1,p.floor.emissivity,p.heat.gasH);
evap = 0;
for pizza=1:2
 theta = 2*pi*((0:N-1)'+.5)/N+p.rotation.initialPhase(pizza) + ...
  2*pi*p.rotation.rpm(pizza)*t/60;
 % Peso posteriore controllabile: rotazione modifica l'esposizione del materiale.
 rear = p.heat.rearExposureMean+p.heat.rearExposureAmplitude*sin(theta);
 for sector=1:N
  ip = i.plate(sector,pizza);
  freeArea = (g.plateArea-double(loaded)*g.pizzaArea)/N;
  surface(ip,freeArea,rear(sector),p.floor.emissivity,p.heat.gasH);
  next = i.plate(mod(sector,N)+1,pizza);
  exchange(ip,next,g.sectorConductance/2*(y(ip)-y(next)));
  ibottom = i.plateBottom(sector,pizza);
  nextBottom = i.plateBottom(mod(sector,N)+1,pizza);
  exchange(ibottom,nextBottom,g.sectorConductance/2*(y(ibottom)-y(nextBottom)));
  if loaded
   ib = i.base(sector,pizza); it = i.top(sector,pizza);
   area = g.pizzaArea/N;
   exchange(ip,ib,p.heat.contactH*area*(y(ip)-y(ib)));
   exchange(ib,it,p.heat.pizzaInternalH*area*(y(ib)-y(it)));
   surface(it,area,rear(sector),p.pizza.emissivity,p.heat.pizzaH);
  end
 end
end
% Il calore latente non puo' superare l'afflusso netto positivo del nodo.
% Finche' l'acqua e' disponibile, la temperatura tende a T_eb+deltaT.
% Sotto la piccola soglia residua il raccordo proporzionale mantiene dm/dt=0
% a massa nulla e permette di passare in modo continuo al riscaldamento asciutto.
if loaded
 for pizza=1:2
  for sector=1:N
   nodes=[i.base(sector,pizza);i.top(sector,pizza)];
   iw=i.water(sector,pizza);
   availability=min(1,max(0,y(iw))/(p.pizza.waterTransitionKg/N));
   activation=min(1,max(0,(y(nodes)-p.pizza.evaporationTemperature)/p.pizza.evaporationTransitionK));
   latent=max(0,q(nodes)).*activation*availability;
   q(nodes)=q(nodes)-latent;
   dy(iw)=-sum(latent)/p.pizza.latentHeat;
   evap=evap+sum(latent);
  end
 end
end
% Due volumi finiti nello spessore: distanze fra centri = spessore/2.
for z=1:2
 exchange(i.shell(z),i.shellOuter(z),g.shellThroughG(z)*(y(i.shell(z))-y(i.shellOuter(z))));
end
floorInner = [i.fixed;i.hearth;i.plate(:)];
floorIds = [i.fixedBottom;i.hearthBottom;i.plateBottom(:)];
for j=1:numel(floorIds)
 exchange(floorInner(j),floorIds(j),g.floorThroughG(j)*(y(floorInner(j))-y(floorIds(j))));
end
% Dispersioni all'ambiente: incluse superfici coperte dalle pizze sotto il piano.
shellLoss = g.shellU*[g.frontShellArea;g.rearShellArea].*(y(i.shellOuter)-Ta);
q(i.shellOuter) = q(i.shellOuter)-shellLoss;
floorAreas = [g.fixedArea;g.rearArea;ones(2*N,1)*g.plateArea/N];
floorLoss = g.floorU*floorAreas.*(y(floorIds)-Ta);
q(floorIds) = q(floorIds)-floorLoss;
openingAreas = [g.mouthArea+g.gapArea;g.hatchArea*p.geom.hatchOpenFraction];
openingLoss = p.heat.openingEmissivity*p.sigma*openingAreas.*(y(i.shell).^4-Ta^4);
q(i.shell) = q(i.shell)-openingLoss;
thermal = g.C>0;
dy(thermal) = q(thermal)./g.C(thermal);
d.fuelPower = fuel;
d.chemicalPower = p.fuel.kgH/3600*p.fuel.lhv;
d.unreleasedPower = d.chemicalPower-fuel;
d.flueLoss = flueLoss;
d.shellLoss = sum(shellLoss);
d.floorLoss = sum(floorLoss);
d.openingLoss = sum(openingLoss);
d.lossPower = flueLoss+sum(shellLoss)+sum(floorLoss)+sum(openingLoss);
d.evapPower = evap;
d.storedPower = sum(g.C.*dy);
d.energyResidual = d.storedPower-(fuel-d.lossPower-evap);
d.massFlow = mdot;
d.draftPa = draft;
d.flueTemperature = y(i.gas(outlet));
% Bi = h_eff*(spessore/2)/k: screening a temperatura istantanea.
hRad = 4*p.sigma*max(y(i.shell))^3*p.floor.emissivity;
d.plateBi = (p.heat.gasH+hRad)*p.floor.thickness/(2*p.floor.k);
d.roofBi = (p.heat.gasH+hRad)*g.roofMaterial.thickness/(2*g.roofMaterial.k);

 function exchange(from,to,power)
  q(from) = q(from)-power;
  q(to) = q(to)+power;
 end
 function surface(node,area,rearWeight,epsilon,h)
  % Scambi reciproci conservativi; vista efficace, non view-factor ray tracing.
  weights = [1-rearWeight rearWeight];
  effectiveEps = 1/(1/p.roof.emissivity+1/epsilon-1);
  for radiationZone=1:2
   exchange(i.gas(radiationZone),node,h*area*weights(radiationZone)*(y(i.gas(radiationZone))-y(node)));
   exchange(i.shell(radiationZone),node,effectiveEps*p.sigma*area*weights(radiationZone)* ...
    (y(i.shell(radiationZone))^4-y(node)^4));
  end
 end
end
