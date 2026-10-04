function a = oven_draft_defaults()
%OVEN_DRAFT_DEFAULTS Scenari assegnati, non coefficienti misurati sul forno.
[p,~]=oven_dimension_defaults();
a.ambientK=p.ambient;
a.chamberK=500+273.15; % gas camera uniforme, non temperatura pietra
a.flueK=250+273.15;    % temperatura media colonna camino, assegnata
a.pressure=p.flow.pressure;
a.gasConstant=287;    % approssimazione aria/fumi, composizione non risolta
a.gravity=p.flow.gravity;
a.roofZ=p.geom.height;
a.inletZ=.03;        % presa bassa posteriore, quota centro ipotizzata
a.doorWidth=p.geom.mouthWidth;
a.doorHeight=p.geom.mouthHeight;
a.doorOpen=false;
a.inletArea=60e-4;   % AREA LIBERA NETTA, non area lorda di una griglia
a.cdInlet=.65;       % ipotesi comprensiva delle perdite di ingresso
a.cdDoor=.65;        % ipotesi distinta dal coefficiente della presa bassa
a.chimneyD=p.flow.chimneyDiameter;
a.chimneyH=p.flow.chimneyHeight;
a.minorK=4;          % raccolta/raccordo/terminale complessivi, ipotesi
a.darcyF=.03;        % fattore Darcy, non Fanning; coefficiente assunto
a.windAdversePa=0;   % pressione aggiunta al terminale rispetto agli ingressi
a.fuelKgH=4.5;       % scenario gia esplorato; consumo continuo, non carica
a.moistureWet=.20;   % umidita su base umida ipotizzata
% USDA Wood as a Fuel: composizione media hardwood secco, incluse ceneri.
a.dryC=.508; a.dryH=.064; a.dryO=.418; a.dryAsh=.01;
a.oxygenMassFraction=.231;
a.cp=p.flow.cp;
a.lhv=p.fuel.lhv;    % PCI della legna tal quale ipotizzato, non ricalcolato
a.efficiency=p.fuel.efficiency;
end
