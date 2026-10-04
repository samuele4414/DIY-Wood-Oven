function report = validate_draft_network(a)
%VALIDATE_DRAFT_NETWORK Controlli numerici, non validazione sperimentale.
checks={};
b=a; b.chamberK=b.ambientK; b.flueK=b.ambientK;
b.fuelKgH=0; b.windAdversePa=0; b.doorOpen=true;
r=oven_draft_network(b);
assert(r.pressureFloorPa==0&&r.stackKgS==0&&r.doorInKgS==0&& ...
 r.doorOutKgS==0&&r.rearInKgS==0&&r.rearOutKgS==0&& ...
 isnan(r.neutralHeightM)&&isnan(r.lambdaTotal));
checks{end+1}='Equilibrio isotermo senza legna e senza vento';
b=a; b.chamberK=max(a.chamberK,a.ambientK+300);
b.flueK=max(a.flueK,a.ambientK+200); b.windAdversePa=0;
b.inletArea=.01; b.doorOpen=true;
r=oven_draft_network(b);
assert(abs(r.massResidualKgS)<1e-9);
checks{end+1}='Conservazione della massa con gas combustibile e bocca aperta';
b.doorOpen=false; closed=oven_draft_network(b);
assert(closed.doorInKgS==0&&closed.doorOutKgS==0&& ...
 abs(closed.massResidualKgS)<1e-9);
checks{end+1}='Porta chiusa: flusso nullo alla bocca';
b.fuelKgH=max(a.fuelKgH,3); full=oven_draft_network(b);
c=b; c.inletArea=1e-7; clogged=oven_draft_network(c);
assert(clogged.rearInKgS<full.rearInKgS&&clogged.lambdaTotal<.01);
checks{end+1}='Ingresso ostruito: carenza aria con combustibile imposto';
b.fuelKgH=0; b.chimneyH=max(.5,a.chimneyH);
short=oven_draft_network(b); c=b; c.chimneyH=2*b.chimneyH;
tall=oven_draft_network(c);
assert(tall.stackKgS>short.stackKgS);
checks{end+1}='Camino piu alto: maggiore portata a porta chiusa';
c=b; c.windAdversePa=.5*short.stackStaticPa; windy=oven_draft_network(c);
c.windAdversePa=short.stackStaticPa+100; reverse=oven_draft_network(c);
assert(windy.stackKgS<short.stackKgS&&reverse.reverseStack&& ...
 reverse.stackKgS<0&&abs(reverse.massResidualKgS)<1e-9);
c.fuelKgH=3; reverseFuel=oven_draft_network(c);
airTheory=reverseFuel.airStoichKgPerKgDry*(1-c.moistureWet)*c.fuelKgH/3600;
assert(reverseFuel.reverseStack && abs(reverseFuel.lambdaTotal- ...
 (reverseFuel.rearInKgS+reverseFuel.doorInKgS-reverseFuel.stackKgS)/airTheory)<1e-10);
checks{end+1}='Vento avverso: riduzione e inversione del tiraggio';
% Camino piccolo: garantisce un piano neutro interno alla bocca aperta.
c=b; c.doorOpen=true; c.chimneyD=.005; c.inletArea=0;
r=oven_draft_network(c);
assert(r.neutralHeightM>0&&r.neutralHeightM<c.doorHeight);
rhoa=c.pressure/(c.gasConstant*c.ambientK);
rhoc=c.pressure/(c.gasConstant*c.chamberK);
beta=c.gravity*(rhoa-rhoc);
dp=@(z)r.pressureFloorPa+beta*z;
% RelTol predefinito (1e-6) domina AbsTol alle portate di questo controllo.
% Imporre entrambi mantiene l'errore di quadratura sotto la soglia del test.
massIn=integral(@(z)c.cdDoor*c.doorWidth*sqrt(2*rhoa*max(-dp(z),0)), ...
 0,c.doorHeight,'Waypoints',r.neutralHeightM,'AbsTol',1e-12,'RelTol',1e-11);
massOut=integral(@(z)c.cdDoor*c.doorWidth*sqrt(2*rhoc*max(dp(z),0)), ...
 0,c.doorHeight,'Waypoints',r.neutralHeightM,'AbsTol',1e-12,'RelTol',1e-11);
assert(abs(r.doorInKgS-massIn)<1e-9&&abs(r.doorOutKgS-massOut)<1e-9);
checks{end+1}='Scambio bidirezionale analitico concorde con quadratura numerica';
c=b; c.dryC=.50; c.dryH=.06; c.dryO=.43; c.dryAsh=.01;
c.oxygenMassFraction=.232; c.moistureWet=.20; c.fuelKgH=4;
r=oven_draft_network(c);
expected=((8/3)*.50+8*.06-.43)/.232;
assert(abs(r.airStoichKgPerKgDry-expected)<1e-12&& ...
 abs(r.lambdaTotal-r.rearInKgS/(expected*.8*4/3600))<1e-10);
checks{end+1}='Aria stechiometrica da C/H/O su legna secca e umidita';
report.passed=true; report.checks=checks;
fprintf('Rete tiraggio: %d verifiche numeriche superate.\n',numel(checks));
end
