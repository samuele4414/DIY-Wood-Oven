function study = run_oven_study(runChecks)
%RUN_OVEN_STUDY Confronti preliminari, un parametro alla volta; nessun ottimo certificato.
if nargin < 1, runChecks = true; end
folder = fileparts(mfilename('fullpath'));
addpath(folder);
out = fullfile(folder,'results');
if ~exist(out,'dir'), mkdir(out); end
% Rigenera grafici/rapporto da uno studio salvato, senza ripetere integrazioni.
if isstruct(runChecks)
    study = runChecks;
    plot_results(study,out);
    write_report(study,out);
    return;
end
if runChecks, validation = oven_validate(); else, validation = []; end
p = oven_defaults();
cases = repmat(p,1,8);
names = {'Acciaio riferimento','Refrattario 30 mm','Volta piana', ...
    'Focolare profondo 24 cm','Camino diametro 13 cm','Camino alto 1 m', ...
    'Camino posteriore','Dischi fermi'};
cases(2).roof.material = 'refractory';
cases(3).geom.roofShape = 'flat';
cases(4).geom.rearDepth = .24;
cases(5).flow.chimneyDiameter = .13;
cases(6).flow.chimneyHeight = 1;
cases(7).flow.chimneyPosition = 'rear';
cases(8).rotation.rpm = [0 0];
results = cell(size(cases));
rows = zeros(numel(cases),11);
for k=1:numel(cases)
    fprintf('Caso %d/%d: %s\n',k,numel(cases),names{k});
    r = oven_simulate(cases(k));
    results{k} = r;
    g = r.g; q = r.p;
    t0 = q.sim.warmupSeconds;
    y0 = interp1(r.t,r.y,t0);
    y60 = interp1(r.t,r.y,t0+60);
    y90 = interp1(r.t,r.y,t0+90);
    meanPlate = mean(r.y(:,g.idx.plate(:)),2)-273.15;
    bake = r.t>=t0 & r.t<=t0+q.sim.bakeSeconds;
    reached = find(meanPlate>=400,1);
    minutes400 = NaN;
    if ~isempty(reached), minutes400 = r.t(reached)/60; end
    rows(k,:) = [mean(y0(g.idx.plate(:)))-273.15, ...
        mean(y0(g.idx.shell))-273.15, ...
        mean(y60(g.idx.base(:)))-273.15,mean(y90(g.idx.base(:)))-273.15, ...
        mean(y90(g.idx.top(:)))-273.15, ...
        max(y90(g.idx.top(:,1)))-min(y90(g.idx.top(:,1))), ...
        mean(y0(g.idx.plate(:)))-273.15-min(meanPlate(bake)), ...
        sum(g.shellMass),sum(g.volume)*1000,minutes400, ...
        sum(y90(g.idx.water(:)))*1000/2];
end
summary = array2table(rows,'VariableNames',{'DischiCarico_C','VoltaCarico_C', ...
    'BasePizza60s_C','BasePizza90s_C','SopraPizza90s_C', ...
    'EscursioneSettoriPizza90s_K','CaloDischi_K','MassaGuscio_kg', ...
    'VolumeCamera_L','TempoDischi400C_min','AcquaResiduaPerPizza_g'});
summary = addvars(summary,string(names(:)),'Before',1,'NewVariableNames','Caso');
writetable(summary,fullfile(out,'confronto_V3.csv'));
study = struct('names',{names},'results',{results},'summary',summary, ...
    'validation',validation,'created',char(datetime('now')));
save(fullfile(out,'study_V3.mat'),'study');
plot_results(study,out);
write_report(study,out);
disp(summary);
fprintf('Risultati: %s\n',out);
end

function plot_results(s,out)
r=s.results{1}; p=r.p; g=r.g;
fig=figure('Visible','off','Color','w','Theme','light','Scrollable','off','Position',[50 50 1400 880]);
guard=onCleanup(@()close(fig));
tiledlayout(2,2,'TileSpacing','compact','Padding','compact');
nexttile;
plot(r.t/60,[mean(r.y(:,g.idx.plate(:)),2),r.y(:,g.idx.fixed), ...
    r.y(:,g.idx.shell)]-273.15,'LineWidth',1.6);
xline(p.sim.warmupSeconds/60,'--','Due pizze');
xlabel('Tempo [min]'); ylabel('Temperatura [°C]'); grid on;
title('Riscaldamento — acciaio di riferimento');
legend('Dischi, superficie','Piano fisso','Guscio anteriore','Guscio posteriore', ...
    'Location','northwest','FontSize',8);
nexttile; hold on;
for k=[1 2 4 5 7]
    z=s.results{k};
    plot(z.t/60,mean(z.y(:,z.g.idx.plate(:)),2)-273.15,'LineWidth',1.5);
end
xlabel('Tempo [min]'); ylabel('Superficie media dischi [°C]'); grid on;
title('Confronti a parità di combustibile');
legend(s.names([1 2 4 5 7]),'Location','northwest','FontSize',8);
nexttile; hold on;
bake=r.t>=p.sim.warmupSeconds & r.t<=p.sim.warmupSeconds+p.sim.bakeSeconds;
bt=r.t(bake)-p.sim.warmupSeconds;
plot(bt,[mean(r.y(bake,g.idx.base(:)),2),mean(r.y(bake,g.idx.top(:)),2)]-273.15,'LineWidth',1.8);
xlabel('Tempo dalla posa [s]'); ylabel('Temperatura nodi pizza [°C]'); grid on;
title('Pizza: nodi equivalenti, non indice di cottura');
legend('Base','Parte superiore','Location','northwest');
nexttile; hold on;
for k=[1 8]
    z=s.results{k};
    ind=z.t>=z.p.sim.warmupSeconds & z.t<=z.p.sim.warmupSeconds+z.p.sim.bakeSeconds;
    v=z.y(ind,z.g.idx.top(:,1));
    plot(z.t(ind)-z.p.sim.warmupSeconds,max(v,[],2)-min(v,[],2),'LineWidth',1.8);
end
xlabel('Tempo dalla posa [s]'); ylabel('Massimo − minimo tra settori [K]'); grid on;
title('Rotazione: effetto del gradiente ipotizzato');
legend('2 giri/min','Dischi fermi','Location','northwest');
exportgraphics(fig,fullfile(out,'confronti_V3.png'),'Resolution',150);
plot_geometry(p,g,out);
end

function plot_geometry(p,g,out)
a=p.geom; W=a.width*100; L=a.frontDepth*100; D=a.rearDepth*100; R=a.rearWidth*100;
fig=figure('Visible','off','Color','w','Theme','light','Scrollable','off','Position',[50 50 1300 720]);
guard=onCleanup(@()close(fig));
tiledlayout(1,2,'TileSpacing','compact','Padding','compact');
nexttile; hold on;
patch([0 W W 0],[0 0 L L],[.91 .85 .70],'EdgeColor',[.3 .3 .3]);
patch([0 W (W+R)/2 (W-R)/2],[L L L+D L+D],[.93 .66 .46],'EdgeColor',[.3 .3 .3]);
theta=linspace(0,2*pi,160);
for k=1:2
    c=a.plateCenters(k,:)*100; rad=a.plateDiameter*50;
    patch(c(1)+rad*cos(theta),c(2)+rad*sin(theta),[.70 .79 .85], ...
        'EdgeColor',[.15 .3 .45],'LineWidth',1.5);
    text(c(1),c(2),sprintf('Disco %d\nØ 32 cm',k),'HorizontalAlignment','center');
end
plot([W/2-a.mouthWidth*50 W/2+a.mouthWidth*50],[0 0],'LineWidth',4,'Color',[.1 .4 .6]);
plot([W/2-a.hatchWidth*50 W/2+a.hatchWidth*50],[L+D L+D],'LineWidth',4,'Color',[.55 .2 .1]);
plot(W/2+5*cos(theta),3+5*sin(theta),'--','Color',[.3 .3 .3],'LineWidth',1.5);
text(W/2,-10,'Bocca — camino sopra la zona anteriore','HorizontalAlignment','center','FontSize',9);
text(W/2,L+D+6,'Botola di carico posteriore','HorizontalAlignment','center');
text(W/2,L+D/2,'Focolare','HorizontalAlignment','center');
axis equal; xlim([-5 W+5]); ylim([-15 L+D+12]);
xlabel('Larghezza [cm]'); ylabel('Profondità [cm]');
title('Pianta interna — riferimento 79 × 55 cm'); grid on;
nexttile; hold on;
xx=linspace(0,W,201); rise=a.rise*100;
if strcmpi(a.roofShape,'flat'),rise=0;end
zz=a.height*100-rise+rise*(1-(2*xx/W-1).^2);
plot(xx,zz,'Color',[.2 .3 .4],'LineWidth',3);
plot(xx,zz+p.insulation.thickness*100,'--','Color',[.6 .6 .6],'LineWidth',2);
plot([0 0],[0 zz(1)],'Color',[.2 .3 .4],'LineWidth',3);
plot([W W],[0 zz(end)],'Color',[.2 .3 .4],'LineWidth',3);
patch([0 W W 0],[0 0 -p.floor.thickness*100 -p.floor.thickness*100],[.91 .85 .70]);
for k=1:2
    c=a.plateCenters(k,1)*100; rad=a.plateDiameter*50;
    plot([c-rad c+rad],[0 0],'LineWidth',5,'Color',[.15 .3 .45]);
end
text(W/2,11,sprintf('Quota massima %.0f cm\nImposta %.0f cm',a.height*100,g.eaveHeight*100),'HorizontalAlignment','center');
text(W/2,-7,'Cordierite 10 mm; giochi radiali provvisori 1 mm','HorizontalAlignment','center','FontSize',9);
axis equal; xlim([-5 W+5]); ylim([-12 max(zz)+12]);
xlabel('Larghezza [cm]'); ylabel('Altezza [cm]'); title('Sezione trasversale — volta parabolica'); grid on;
exportgraphics(fig,fullfile(out,'geometria_V3.png'),'Resolution',150);
end

function write_report(s,out)
fid=fopen(fullfile(out,'RISULTATI_V3.md'),'w','n','UTF-8');
assert(fid>=0,'Impossibile scrivere il rapporto.');
guard=onCleanup(@()fclose(fid));
p=s.results{1}.p; g=s.results{1}.g;
fprintf(fid,'# Confronti preliminari forno V3\n\nGenerato: %s.\n\n',s.created);
fprintf(fid,['Modello non calibrato. Le temperature delle pizze sono medie di nodi equivalenti; ' ...
    'non descrivono la doratura, il cornicione o una pizza cotta. Nessuna configurazione viene ' ...
    'dichiarata ottimale o pronta per la costruzione.\n\n']);
fprintf(fid,['Condizioni comuni: %.1f kg/h di legna, PCI %.1f MJ/kg, efficienza %.2f; ' ...
    '%.1f kW introdotti nel modello. Riscaldamento %.0f minuti, due pizze da %.0f cm e %.0f g ' ...
    'per %.0f s, poi %.0f s di recupero a fuoco acceso.\n\n'], ...
    p.fuel.kgH,p.fuel.lhv/1e6,p.fuel.efficiency,p.fuel.kgH/3600*p.fuel.lhv*p.fuel.efficiency/1000, ...
    p.sim.warmupSeconds/60,p.pizza.diameter*100,p.pizza.mass*1000,p.sim.bakeSeconds,p.sim.recoverySeconds);
fprintf(fid,'Piano fisso %.4f m²; due dischi %.4f m²; giochi %.4f m²; totale %.4f m².\n\n', ...
    g.fixedArea,2*g.plateArea,g.gapArea,g.frontArea);
fprintf(fid,'| Caso | Dischi al carico °C | Base pizza 90 s °C | Sopra pizza 90 s °C | Escursione settori K | Acqua per pizza a 90 s, g | Massa guscio kg |\n');
fprintf(fid,'|---|---:|---:|---:|---:|---:|---:|\n');
for k=1:height(s.summary)
    v=s.summary(k,:);
    fprintf(fid,'| %s | %.1f | %.1f | %.1f | %.2f | %.2f | %.1f |\n',char(v.Caso), ...
        v.DischiCarico_C,v.BasePizza90s_C,v.SopraPizza90s_C,v.EscursioneSettoriPizza90s_K, ...
        v.AcquaResiduaPerPizza_g,v.MassaGuscio_kg);
end
dry = s.summary.AcquaResiduaPerPizza_g<.01*p.pizza.mass*p.pizza.waterFraction*1000;
if any(dry)
    fprintf(fid,['\n**Limite emerso nella simulazione:** acqua quasi esaurita nei casi: %s. ' ...
        'La disponibilita immediata di acqua nel modello puo sovrastimare la velocita di asciugatura. ' ...
        'Le temperature successive non sono una previsione affidabile della pizza reale.\n'], ...
        strjoin(s.names(dry),', '));
end
if isstruct(s.validation) && isfield(s.validation,'passed')
    fprintf(fid,'\nVerifiche numeriche: %d superate; residuo massimo %.3g W; differenza di convergenza %.4g K.\n', ...
        numel(s.validation.checks),s.validation.maxEnergyResidualW,s.validation.convergenceMaxK);
end
fprintf(fid,['\nIl confronto a 30 minuti include il diverso transitorio: una volta refrattaria ' ...
    'più fredda a questo istante non implica prestazioni peggiori dopo un preriscaldamento più lungo. ' ...
    'Il caso con focolare più profondo mantiene identica potenza di combustione. Il caso a volta ' ...
    'piana mantiene identica altezza massima: cambiano area e volume.\n\n' ...
    'La posizione del camino modifica la rete di trasporto tra due zone. Non risolve il campo di velocità, ' ...
    'il passaggio di fiamma sotto la volta, il vento o la fuoriuscita di fumo dalla bocca. ' ...
    'Il confronto rotante/fermo dipende dal gradiente di esposizione imposto nei parametri.\n\n' ...
    'File: confronto_V3.csv per i dati; study_V3.mat per tutti gli stati, parametri e diagnostiche; ' ...
    'confronti_V3.png e geometria_V3.png per i grafici.\n']);
end
