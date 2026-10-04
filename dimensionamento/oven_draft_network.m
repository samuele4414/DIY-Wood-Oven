function r = oven_draft_network(a)
%OVEN_DRAFT_NETWORK Rete di pressione 1D a temperature assegnate, non CFD.
% Quote dal piano; H camino dal tetto al terminale. Vento positivo avverso.
% Combustibile imposto: lambda basso NON riduce automaticamente la fiamma.
positive={'ambientK','chamberK','flueK','pressure','gasConstant','gravity', ...
 'roofZ','doorWidth','doorHeight','cdInlet','cdDoor','chimneyD', ...
 'minorK','oxygenMassFraction','cp','lhv'};
nonnegative={'inletZ','inletArea','chimneyH','darcyF','fuelKgH', ...
 'moistureWet','dryC','dryH','dryO','dryAsh','efficiency'};
for k=1:numel(positive)
 v=a.(positive{k});
 assert(isnumeric(v)&&isreal(v)&&isscalar(v)&&isfinite(v)&&v>0, ...
  'oven:draft','Parametro positivo finito richiesto: %s.',positive{k});
end
for k=1:numel(nonnegative)
 v=a.(nonnegative{k});
 assert(isnumeric(v)&&isreal(v)&&isscalar(v)&&isfinite(v)&&v>=0, ...
  'oven:draft','Parametro non negativo finito richiesto: %s.',nonnegative{k});
end
assert(isnumeric(a.windAdversePa)&&isreal(a.windAdversePa)&& ...
 isscalar(a.windAdversePa)&&isfinite(a.windAdversePa), ...
 'oven:draft','Pressione vento finita richiesta.');
assert(isscalar(a.doorOpen)&&ismember(a.doorOpen,[0 1])&& ...
 a.chamberK>=a.ambientK&&a.inletZ<=a.roofZ&&a.doorHeight<=a.roofZ&& ...
 a.moistureWet<1&&a.efficiency<=1&&a.oxygenMassFraction<=1&& ...
 a.cdInlet<=1&&a.cdDoor<=1&& ...
 abs(a.dryC+a.dryH+a.dryO+a.dryAsh-1)<1e-8, ...
 'oven:draft','Quote, temperature, coefficienti o frazioni incompatibili.');
rhoa=a.pressure/(a.gasConstant*a.ambientK);
rhoc=a.pressure/(a.gasConstant*a.chamberK);
rhof=a.pressure/(a.gasConstant*a.flueK);
beta=a.gravity*(rhoa-rhoc);
stackHead=a.gravity*a.chimneyH*(rhoa-rhof);
area=pi*a.chimneyD^2/4;
loss=a.minorK+a.darcyF*a.chimneyH/a.chimneyD;
fuel=a.fuelKgH/3600;
fuelGas=fuel*(1-(1-a.moistureWet)*a.dryAsh);
stoich=((8/3)*a.dryC+8*a.dryH-a.dryO)/a.oxygenMassFraction;
assert(stoich>0,'oven:draft','Richiesta stechiometrica di ossigeno positiva.');
bound=max(1,abs(stackHead)+beta*a.roofZ+abs(a.windAdversePa));
for k=1:80
 if balance(-bound)>=0 && balance(bound)<=0, break; end
 bound=2*bound;
end
assert(balance(-bound)>=0&&balance(bound)<=0,'oven:draft', ...
 'Impossibile delimitare la soluzione della rete.');
lo=-bound; hi=bound;
for k=1:160
 p0=(lo+hi)/2; residual=balance(p0);
 if residual==0 || hi-lo<1e-12, break; end
 if residual>0, lo=p0; else, hi=p0; end
end
[~,ri,ro,di,do,ms,drive]=balance(p0);
r.pressureFloorPa=p0;
r.pressureDoorTopPa=p0+beta*a.doorHeight;
r.stackDrivePa=drive;
r.stackStaticPa=beta*(a.roofZ-a.inletZ)+stackHead;
r.rearInKgS=ri; r.rearOutKgS=ro;
r.doorInKgS=di; r.doorOutKgS=do;
r.stackKgS=ms; r.massResidualKgS=ri+di+fuelGas-ro-do-ms;
r.airStoichKgPerKgDry=stoich;
airRequired=stoich*(1-a.moistureWet)*fuel;
r.lambdaTotal=NaN; r.lambdaRear=NaN;
if airRequired>0
 % Totale degli ingressi d'aria, anche dal camino in inversione: non prova
 % che questa aria raggiunga il combustibile o partecipi alla combustione.
 r.lambdaTotal=(ri+di+max(-ms,0))/airRequired; r.lambdaRear=ri/airRequired;
end
r.neutralHeightM=NaN;
if beta>1e-10, r.neutralHeightM=-p0/beta; end
upstream=rhof;
if ms<0, upstream=rhoa; end
r.stackVelocityMS=ms/(upstream*area);
r.sensibleChamberKW=(max(ms,0)+ro+do)*a.cp*(a.chamberK-a.ambientK)/1000;
r.fuelReleasedKW=fuel*a.lhv*a.efficiency/1000;
% Tutti i gas escono dal volume camera a chamberK; flueK serve alla densita
% media nel tubo, il cui raffreddamento e esterno a questo volume. Confronto
% condizionato a queste temperature: non include pareti, pizza o radiazione.
r.requiresStoredHeat=r.sensibleChamberKW>r.fuelReleasedKW;
r.reverseStack=ms<0; % Inversione: scenario caldo non valido per il progetto.

 function [res,ri,ro,di,dout,ms,drive]=balance(p)
  inlet=p+beta*a.inletZ;
  ri=a.cdInlet*a.inletArea*sqrt(2*rhoa*max(-inlet,0));
  ro=a.cdInlet*a.inletArea*sqrt(2*rhoc*max(inlet,0));
  di=0; dout=0;
  if a.doorOpen
   [intIn,intOut]=doorIntegrals(p,beta,a.doorHeight);
   di=a.cdDoor*a.doorWidth*sqrt(2*rhoa)*intIn;
   dout=a.cdDoor*a.doorWidth*sqrt(2*rhoc)*intOut;
  end
  drive=p+beta*a.roofZ+stackHead-a.windAdversePa;
  rho=rhof;
  if drive<0, rho=rhoa; end
  ms=sign(drive)*area*sqrt(2*rho*abs(drive)/loss);
  res=ri+di+fuelGas-ro-dout-ms;
 end
end

function [intIn,intOut]=doorIntegrals(p,beta,h)
% Integrali esatti di sqrt(|deltaP|), separati al piano neutro.
if beta<=1e-10
 intIn=h*sqrt(max(-p,0)); intOut=h*sqrt(max(p,0)); return;
end
crossing=min(h,max(0,-p/beta));
intIn=segment(crossing,max(-p,0),max(-(p+beta*crossing),0));
intOut=segment(h-crossing,max(p+beta*crossing,0),max(p+beta*h,0));
end

function value=segment(lengthZ,q0,q1)
% Forma stabile anche con pressioni quasi uguali ai due estremi.
den=sqrt(q0)+sqrt(q1);
value=0;
if den>0, value=(2/3)*lengthZ*(q0+sqrt(q0*q1)+q1)/den; end
end
