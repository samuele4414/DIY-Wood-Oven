function g = oven_geometry(p)
%OVEN_GEOMETRY Geometria e capacita' senza duplicare l'area dei dischi.
a = p.geom; N = a.sectors;
positive = [p.ambient p.floor.thickness p.floor.rho p.floor.cp p.floor.k ...
 p.insulation.k p.insulation.outsideH p.pizza.mass p.pizza.cp ...
 p.pizza.initialTemperature p.pizza.latentHeat p.pizza.evaporationTemperature ...
 p.pizza.evaporationTransitionK p.pizza.waterTransitionKg ...
 p.flow.pressure p.flow.gasConstant p.flow.gravity p.flow.cp p.fuel.lhv];
assert(isreal(positive) && all(isfinite(positive)) && all(positive>0), ...
 'oven:parameters','Proprieta'' fisiche finite e positive richieste.');
nonnegative = [p.insulation.thickness p.fuel.kgH p.flow.mixingKgS ...
 p.heat.gasH p.heat.pizzaH p.heat.contactH p.heat.pizzaInternalH ...
 p.heat.shellLink];
assert(isreal(nonnegative) && all(isfinite(nonnegative)) && all(nonnegative>=0), ...
 'oven:parameters','Coefficienti di scambio e sorgenti non possono essere negativi.');
fractions = [p.fuel.efficiency p.fuel.radiantFraction p.pizza.waterFraction p.flow.inletFraction];
assert(all(isfinite(fractions)) && all(fractions>=0 & fractions<=1) && ...
 p.pizza.baseMassFraction>0 && p.pizza.baseMassFraction<1, ...
 'oven:parameters','Frazioni fisiche fuori intervallo.');
emissivities = [p.floor.emissivity p.roof.emissivity p.pizza.emissivity p.heat.openingEmissivity];
assert(all(isfinite(emissivities)) && all(emissivities>0 & emissivities<=1), ...
 'oven:parameters','Emissivita'' nell''intervallo (0,1] richieste.');
assert(numel(p.rotation.rpm)==2 && numel(p.rotation.initialPhase)==2 && ...
 isreal(p.rotation.rpm) && isreal(p.rotation.initialPhase) && ...
 all(isfinite([p.rotation.rpm(:);p.rotation.initialPhase(:)])), ...
 'oven:parameters','Rotazione: due velocita'' e due fasi finite richieste.');
assert(isfinite(p.heat.rearExposureMean) && isfinite(p.heat.rearExposureAmplitude) && ...
 p.heat.rearExposureAmplitude>=0 && p.heat.rearExposureMean-p.heat.rearExposureAmplitude>=0 && ...
 p.heat.rearExposureMean+p.heat.rearExposureAmplitude<=1, ...
 'oven:parameters','Esposizione posteriore deve restare fra zero e uno.');
assert(all([a.width a.frontDepth a.rearWidth a.rearDepth a.height ...
 a.plateDiameter p.floor.thickness p.pizza.mass p.pizza.cp] > 0), ...
 'oven:geometry','Dimensioni e proprieta'' devono essere positive.');
assert(N >= 4 && N == floor(N),'oven:geometry','Servono almeno 4 settori.');
assert(isequal(size(a.plateCenters),[2 2]),'oven:geometry','Occorrono due centri x,y.');
assert(a.plateClearance >= 0 && p.pizza.diameter > 0 && ...
 p.pizza.diameter <= a.plateDiameter,'oven:geometry','Pizza/disco o gioco non validi.');
r = a.plateDiameter/2; re = r+a.plateClearance;
assert(all(a.plateCenters(:,1)-re >= 0) && all(a.plateCenters(:,1)+re <= a.width) && ...
 all(a.plateCenters(:,2)-re >= 0) && all(a.plateCenters(:,2)+re <= a.frontDepth), ...
 'oven:geometry','Un disco con il gioco esce dal piano anteriore.');
assert(norm(diff(a.plateCenters,1,1)) >= 2*re,'oven:geometry','I dischi si sovrappongono.');
assert(a.mouthWidth>0 && a.mouthWidth<=a.width && a.mouthHeight>0, ...
 'oven:geometry','Bocca non valida.');
assert(a.hatchWidth>0 && a.hatchWidth<=a.rearWidth && a.hatchHeight>0 && ...
 a.hatchOpenFraction>=0 && a.hatchOpenFraction<=1,'oven:geometry','Botola non valida.');
switch lower(a.roofShape)
 case 'flat', rise = 0;
 case 'barrel', rise = a.rise;
 otherwise, error('oven:geometry','roofShape deve essere flat o barrel.');
end
assert(rise>=0 && rise<a.height,'oven:geometry','Freccia della volta non valida.');
g.eaveHeight = a.height-rise;
assert(a.mouthHeight<=g.eaveHeight && a.hatchHeight<=g.eaveHeight, ...
 'oven:geometry','Apertura piu'' alta dell''imposta: geometria non supportata.');
g.frontArea = a.width*a.frontDepth;
g.rearArea = (a.width+a.rearWidth)*a.rearDepth/2;
g.plateArea = pi*r^2;
g.gapArea = 2*pi*(re^2-r^2);
g.fixedArea = g.frontArea-2*g.plateArea-g.gapArea;
g.pizzaArea = pi*p.pizza.diameter^2/4;
g.totalArea = g.frontArea+g.rearArea;
% Volta z=h_imposta+rise*(1-(2*x/w)^2); w varia linearmente sul retro.
u = linspace(-1,1,101);
g.frontRoofArea = a.frontDepth*a.width/2*trapz(u,sqrt(1+(4*rise*u/a.width).^2));
ys = linspace(0,a.rearDepth,101);
ws = a.width+(a.rearWidth-a.width)*ys/a.rearDepth;
slices = zeros(size(ys));
for j=1:numel(ys)
 dzdx = -4*rise*u/ws(j);
 dzdy = 2*rise*u.^2*(a.rearWidth-a.width)/(a.rearDepth*ws(j));
 slices(j) = ws(j)/2*trapz(u,sqrt(1+dzdx.^2+dzdy.^2));
end
g.rearRoofArea = trapz(ys,slices);
g.mouthArea = a.mouthWidth*a.mouthHeight;
g.hatchArea = a.hatchWidth*a.hatchHeight;
g.frontShellArea = g.frontRoofArea+2*a.frontDepth*g.eaveHeight + ...
 a.width*(g.eaveHeight+2*rise/3)-g.mouthArea;
rearSide = hypot(a.rearDepth,(a.width-a.rearWidth)/2);
g.rearShellArea = g.rearRoofArea+2*rearSide*g.eaveHeight + ...
 a.rearWidth*(g.eaveHeight+2*rise/3)-g.hatchArea*a.hatchOpenFraction;
g.volume = [g.frontArea g.rearArea]*(g.eaveHeight+2*rise/3);
g.chimneyArea = pi*p.flow.chimneyDiameter^2/4;
g.inletArea = p.flow.inletFraction*g.mouthArea+a.hatchOpenFraction*g.hatchArea;
assert(g.inletArea>0 && all([p.flow.chimneyDiameter p.flow.chimneyHeight ...
 p.flow.chimneyLoss p.flow.inletLoss p.flow.cp] > 0), ...
 'oven:geometry','Geometria camino/ingresso non valida.');
assert(any(strcmpi(p.flow.chimneyPosition,{'front','rear'})), ...
 'oven:geometry','Posizione camino non valida.');
assert(any(strcmpi(p.roof.material,{'steel','refractory'})), ...
 'oven:geometry','Materiale volta non valido.');
m = p.roof.(lower(p.roof.material));
props = [m.thickness m.rho m.cp m.k];
assert(isreal(props) && all(isfinite(props)) && all(props>0), ...
 'oven:parameters','Proprieta'' materiale volta finite e positive richieste.');
g.roofMaterial = m;
g.shellMass = [g.frontShellArea g.rearShellArea]*m.thickness*m.rho;
g.cordieriteMass = [g.fixedArea g.rearArea g.plateArea g.plateArea]*p.floor.thickness*p.floor.rho;
rho0 = p.flow.pressure/(p.flow.gasConstant*p.ambient);
g.idx.gas = [1 2]; g.idx.shell = [3 4]; g.idx.fixed = 5; g.idx.hearth = 6;
g.idx.plate = reshape(7:6+2*N,N,2);
g.idx.base = reshape(7+2*N:6+4*N,N,2);
g.idx.top = reshape(7+4*N:6+6*N,N,2);
g.idx.water = reshape(7+6*N:6+8*N,N,2);
g.idx.plateBottom = reshape(7+8*N:6+10*N,N,2);
g.idx.shellOuter = 7+10*N:8+10*N;
g.idx.fixedBottom = 9+10*N;
g.idx.hearthBottom = 10+10*N;
g.nStates = 10+10*N;
g.C = zeros(g.nStates,1);
g.C(g.idx.gas) = rho0*g.volume*p.flow.cp; % masse efficaci fisse
g.C(g.idx.shell) = g.shellMass*m.cp;
g.C(g.idx.fixed) = g.cordieriteMass(1)*p.floor.cp;
g.C(g.idx.hearth) = g.cordieriteMass(2)*p.floor.cp;
g.C(g.idx.plate(:)) = g.plateArea*p.floor.thickness*p.floor.rho*p.floor.cp/N;
g.C(g.idx.base(:)) = p.pizza.mass*p.pizza.cp*p.pizza.baseMassFraction/N;
g.C(g.idx.top(:)) = p.pizza.mass*p.pizza.cp*(1-p.pizza.baseMassFraction)/N;
assert(all(g.C(1:6+6*N)>0),'oven:geometry','Capacita'' termiche non positive.');
inner = [g.idx.plate(:);g.idx.shell(:);g.idx.fixed;g.idx.hearth];
outer = [g.idx.plateBottom(:);g.idx.shellOuter(:);g.idx.fixedBottom;g.idx.hearthBottom];
g.C(inner) = g.C(inner)/2;
g.C(outer) = g.C(inner);
g.shellU = 1/(m.thickness/(4*m.k)+p.insulation.thickness/p.insulation.k+1/p.insulation.outsideH);
g.floorU = 1/(p.floor.thickness/(4*p.floor.k)+p.insulation.thickness/p.insulation.k+1/p.insulation.outsideH);
g.shellThroughG = 2*m.k*[g.frontShellArea;g.rearShellArea]/m.thickness;
g.floorThroughG = 2*p.floor.k*[g.fixedArea;g.rearArea;ones(2*N,1)*g.plateArea/N]/p.floor.thickness;
% Accoppiamento fra settori adiacenti: rete circolare equivalente.
g.sectorConductance = p.floor.k*p.floor.thickness*N/(2*pi);
g.labels = {'gas_front','gas_rear','shell_front','shell_rear','floor_fixed','hearth'};
for kind={'plate','base','top','water'}
 for pizza=1:2
  for sector=1:N
   g.labels{end+1} = sprintf('%s_%d_sector_%d',kind{1},pizza,sector);
  end
 end
end
for pizza=1:2
 for sector=1:N
  g.labels{end+1} = sprintf('plate_bottom_%d_sector_%d',pizza,sector);
 end
end
g.labels = [g.labels {'shell_outer_front','shell_outer_rear','floor_fixed_bottom','hearth_bottom'}];
g.y0 = p.ambient*ones(g.nStates,1);
g.y0([g.idx.base(:);g.idx.top(:)]) = p.pizza.initialTemperature;
g.y0(g.idx.water(:)) = p.pizza.mass*p.pizza.waterFraction/N;
end
