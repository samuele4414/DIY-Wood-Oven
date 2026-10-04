function draw_dimension_study(study)
%DRAW_DIMENSION_STUDY Quote geometriche in cm, non disegni esecutivi.
folder=fileparts(mfilename('fullpath'));
out=fullfile(folder,'results');
if ~exist(out,'dir'), mkdir(out); end
p=study.p; d=study.d; g=study.g;
plan(p,d,g,out);
sections(p,d,g,out);
if isfield(study,'results') && any(~cellfun(@isempty,study.results))
    thermal(study,out);
end
end

function plan(p,d,g,out)
a=p.geom; W=100*a.width; L=100*a.frontDepth;
R=100*a.rearWidth; F=100*a.rearDepth; H=100*d.hoodDepth;
fig=figure('Visible','off','Theme','light','Color','w', ...
    'Scrollable','off','Position',[50 50 900 1020]);
guard=onCleanup(@()close(fig));
axes(fig,'Position',[.11 .08 .83 .85]); hold on;
hx=100*g.hoodX;
patch([hx(1) hx(2) hx(2) hx(1)],[-H -H 0 0],[.87 .92 .96],'EdgeColor',[.2 .3 .4]);
patch([0 W W 0],[0 0 L L],[.94 .88 .72],'EdgeColor',[.3 .3 .3]);
patch([0 W (W+R)/2 (W-R)/2],[L L L+F L+F],[.97 .78 .58], ...
    'EdgeColor',[.3 .3 .3]);
theta=linspace(0,2*pi,180);
for k=1:2
    c=100*a.plateCenters(k,:); rad=50*a.plateDiameter;
    patch(c(1)+rad*cos(theta),c(2)+rad*sin(theta),[.71 .83 .89], ...
        'EdgeColor',[.13 .34 .45],'LineWidth',1.5);
    text(c(1),c(2),sprintf('Disco %d\nØ %.0f cm',k,100*a.plateDiameter), ...
        'HorizontalAlignment','center','FontSize',11);
    plot(c(1),c(2),'+','Color',[.13 .34 .45],'MarkerSize',7);
end
for k=1:size(g.woodRows,1)
    b=100*g.woodRows(k,:);
    patch([b(1) b(2) b(2) b(1)],[b(3) b(3) b(4) b(4)], ...
        [.61 .35 .16],'EdgeColor',[.35 .19 .08]);
    text(mean(b(1:2)),mean(b(3:4)),sprintf('Legna %.0f cm',100*d.woodLength), ...
        'HorizontalAlignment','center','Color','w','FontSize',10);
end
mouthX=(W+[-1 1]*100*a.mouthWidth)/2;
plot(mouthX,[0 0],'--','Color',[.4 .4 .4],'LineWidth',1);
plot(mouthX,100*g.doorSeatY*[1 1],'Color',[.36 .2 .54],'LineWidth',3);
text(W/2,1.9,'Passaggio camera–cappa sempre aperto', ...
    'HorizontalAlignment','center','FontSize',9,'Color',[.3 .3 .3]);
text(W/2,100*g.doorSeatY-3,sprintf('Porta frontale / battuta — luce %.0f cm',100*a.mouthWidth), ...
    'HorizontalAlignment','center','FontSize',10,'Color',[.28 .12 .44]);
fc=100*g.flueCenter;
plot(fc(1)+50*d.collarDiameter*cos(theta),fc(2)+50*d.collarDiameter*sin(theta), ...
    '--','Color',[.35 .35 .35],'LineWidth',1.3);
patch(fc(1)+50*p.flow.chimneyDiameter*cos(theta), ...
    fc(2)+50*p.flow.chimneyDiameter*sin(theta),[.65 .74 .79], ...
    'EdgeColor',[.18 .27 .33],'LineWidth',1.4);
plot(fc(1),fc(2),'+','Color',[.18 .27 .33]);
text(3,-H/2,sprintf('Raccolta\nfumi'),'FontSize',11);
text(fc(1)+50*d.collarDiameter+3,fc(2), ...
    sprintf('Camino Ø %.0f\nRaccordo Ø %.0f',100*p.flow.chimneyDiameter,100*d.collarDiameter), ...
    'FontSize',9);
hatchX=(W+[-1 1]*100*a.hatchWidth)/2;
plot(hatchX,[L+F L+F],'Color',[.6 .18 .10],'LineWidth',4);
text(W/2,L+F+3,sprintf('Botola posteriore %.0f × %.0f cm',100*a.hatchWidth,100*a.hatchHeight), ...
    'HorizontalAlignment','center','FontSize',10);
dimV(-6,-H,0,sprintf('%.0f',H));
dimV(-6,0,L,sprintf('%.0f',L));
dimV(-6,L,L+F,sprintf('%.0f',F));
dimV(-14,-H,L+F,sprintf('Totale %.0f cm',H+L+F));
dimH(0,W,L+F+10,sprintf('Piano largo %.0f cm',W));
% Distanza operativa dalla bocca esterna al bordo anteriore dei dischi.
dimV(W+6,-H,100*(a.plateCenters(1,2)-a.plateDiameter/2), ...
    sprintf('%.1f cm',100*g.frontedgeToPlateNear(1)));
axis equal; xlim([-20 W+15]); ylim([-H-9 L+F+15]);
axis off;
title({'Pianta proposta — quote interne';'Piano 79 × 41 cm + raccolta fumi + zona legna'},'FontSize',13);
exportgraphics(fig,fullfile(out,'pianta_quotata.png'),'Resolution',150);
end

function sections(p,d,g,out)
a=p.geom; W=100*a.width; L=100*a.frontDepth;
F=100*a.rearDepth; H=100*d.hoodDepth; z=100*a.height;
fig=figure('Visible','off','Theme','light','Color','w', ...
    'Scrollable','off','Position',[50 50 1400 680]);
guard=onCleanup(@()close(fig));
tiledlayout(1,2,'Padding','loose','TileSpacing','loose');
nexttile; hold on;
total=H+L+F; mouthHeight=100*a.mouthHeight;
patch([H H+L H+L H],[0 0 -1 -1],[.94 .88 .72]);
patch([0 H H 0],[0 0 -1 -1],[.87 .92 .96]);
patch([H+L total total H+L],[0 0 -1 -1],[.97 .78 .58]);
plot([H total],[z z],'Color',[.2 .3 .4],'LineWidth',2);
plot([total total],[0 z],'Color',[.2 .3 .4],'LineWidth',2);
plot([H H],[mouthHeight z],'Color',[.35 .35 .35],'LineWidth',3);
doorX=H+100*g.doorSeatY;
plot([doorX doorX],[0 mouthHeight],'Color',[.36 .2 .54],'LineWidth',5);
plot([doorX doorX],[mouthHeight z],'Color',[.2 .3 .4],'LineWidth',2);
text(doorX-3,mouthHeight/2,'Porta chiusa','Rotation',90, ...
    'HorizontalAlignment','center','FontSize',9,'Color',[.36 .2 .54]);
xc=H+100*g.flueCenter(2); rr=50*p.flow.chimneyDiameter;
plot([0 xc-rr],[z z],'Color',[.2 .3 .4],'LineWidth',2);
plot([xc+rr H],[z z],'Color',[.2 .3 .4],'LineWidth',2);
plot([xc-rr xc-rr],[z z+16],'Color',[.2 .3 .4],'LineWidth',2);
plot([xc+rr xc+rr],[z z+16],'Color',[.2 .3 .4],'LineWidth',2);
text(xc,z+19,'Camino','HorizontalAlignment','center','FontSize',10);
% Frecce di sola connessione geometrica, non un campo di moto calcolato.
flowZ=.65*mouthHeight; flowStart=H+L*.55;
quiver(flowStart,flowZ,xc-flowStart,0,0,'Color',[.72 .35 .09], ...
    'LineWidth',1.5,'MaxHeadSize',.3);
quiver(xc,flowZ,0,z+8-flowZ,0,'Color',[.72 .35 .09], ...
    'LineWidth',1.5,'MaxHeadSize',.3);
text(H+L/2,flowZ+3.5,'Passaggio aperto','HorizontalAlignment','center','FontSize',9);
plateNear=H+100*(a.plateCenters(1,2)-a.plateDiameter/2);
plateFar=H+100*(a.plateCenters(1,2)+a.plateDiameter/2);
plot([plateNear plateFar],[.5 .5],'--','Color',[.13 .34 .45],'LineWidth',3);
text((plateNear+plateFar)/2,6,'Dischi in proiezione','HorizontalAlignment','center','FontSize',9);
for k=1:size(g.woodRows,1)
    lo=H+100*g.woodRows(k,3); hi=H+100*g.woodRows(k,4);
    patch([lo hi hi lo],[0 0 100*d.woodThickness 100*d.woodThickness], ...
        [.61 .35 .16],'EdgeColor',[.35 .19 .08]);
end
text(H+L/2,z-6,sprintf('Camera H %.0f cm',z),'HorizontalAlignment','center','FontSize',10);
dimH(0,H,-6,sprintf('Cappa %.0f',H));
dimH(H,H+L,-6,sprintf('%.0f',L));
dimH(H+L,total,-6,sprintf('%.0f',F));
dimH(doorX,plateNear,-14,sprintf('Porta → disco %.1f cm',100*g.frontedgeToPlateNear(1)));
dimV(total+6,0,z,sprintf('%.0f',z));
axis equal; xlim([-10 total+13]); ylim([-21 z+23]); axis off;
title({'Sezione longitudinale centrale';'Porta chiusa, collegamento fumi schematico'},'FontSize',12);
nexttile; hold on;
xx=linspace(0,W,200);
zz=z-100*a.rise+100*a.rise*(1-(2*xx/W-1).^2);
plot(xx,zz,'Color',[.2 .3 .4],'LineWidth',2.5);
plot([0 0],[0 zz(1)],'Color',[.2 .3 .4],'LineWidth',2);
plot([W W],[0 zz(end)],'Color',[.2 .3 .4],'LineWidth',2);
patch([0 W W 0],[0 0 -1 -1],[.94 .88 .72]);
mw=100*a.mouthWidth;
mx=(W-mw)/2;
plot([mx mx mx+mw mx+mw],[0 mouthHeight mouthHeight 0], ...
    'Color',[.4 .4 .4],'LineWidth',2);
for k=1:2
    xc=100*a.plateCenters(k,1); r=50*a.plateDiameter;
    plot([xc-r xc+r],[0 0],'Color',[.13 .34 .45],'LineWidth',4);
end
text(W/2,9,sprintf('Passaggio aperto %.0f × %.0f cm',mw,mouthHeight), ...
    'HorizontalAlignment','center','FontSize',11,'Color',[.3 .3 .3]);
text(W/2,z+4,sprintf('Volta %.0f cm — imposta %.0f cm',z,100*g.core.eaveHeight), ...
    'HorizontalAlignment','center','FontSize',10);
dimH(mx,mx+mw,-6,sprintf('%.0f',mw));
dimV(W+5,0,mouthHeight,sprintf('%.0f',mouthHeight));
axis equal; xlim([-4 W+12]); ylim([-15 z+13]); axis off;
title({'Sezione frontale della camera';'Dimensioni di confronto, non esecutive'},'FontSize',12);
exportgraphics(fig,fullfile(out,'sezioni_quotate.png'),'Resolution',150);
end

function thermal(s,out)
fig=figure('Visible','off','Theme','light','Color','w', ...
    'Scrollable','off','Position',[50 50 1400 700]);
guard=onCleanup(@()close(fig));
tiledlayout(1,2,'Padding','loose','TileSpacing','loose');
nexttile; hold on;
chosen=unique([1 4 11 12 13]); chosen=chosen(chosen<=numel(s.results));
palette=lines(numel(chosen));
leg=cell(1,numel(chosen));
for n=1:numel(chosen)
    k=chosen(n);
    h=s.preheat{k};
    plot(h.t/60,h.plateC,'LineWidth',1.6,'Color',palette(n,:));
    leg{n}=caseLabel(s.names{k});
end
yline(s.d.targetPlateC,'--','Soglia comune');
xlabel('Tempo da accensione [min]'); ylabel('Temperatura media superiore dischi [°C]');
title('Confronto a pari temperatura di carico'); grid on;
legend(leg,'Location','southeast','FontSize',9);
nexttile; hold on; leg=cell(1,numel(chosen));
for n=1:numel(chosen)
    k=chosen(n);
    if isempty(s.results{k}), continue; end
    r=s.results{k}; t0=r.p.sim.warmupSeconds;
    sel=r.t>=t0 & r.t<=t0+r.p.sim.bakeSeconds;
    plot(r.t(sel)-t0,mean(r.y(sel,r.g.idx.plate(:)),2)-273.15, ...
        'LineWidth',1.6,'Color',palette(n,:));
    leg{n}=caseLabel(s.names{k});
end
xlabel('Tempo con due pizze [s]'); ylabel('Temperatura media superiore dischi [°C]');
title('Calo del piano durante il carico — modello non calibrato'); grid on;
legend(leg(~cellfun(@isempty,leg)),'Location','southwest','FontSize',9);
exportgraphics(fig,fullfile(out,'confronto_a_450C.png'),'Resolution',150);
end

function label=caseLabel(name)
switch name
    case 'candidato_25cm', label='Base: 3,5 kg/h, focolare 25 cm';
    case 'focolare_30cm', label='Focolare 30 cm, 3,5 kg/h';
    case 'volta_refrattaria', label='Guscio refrattario, 3,5 kg/h';
    case 'legna_4_5kg_h', label='4,5 kg/h, pietra 10 mm';
    case 'legna_4_5kg_h_pietra_20mm', label='4,5 kg/h, pietra 20 mm';
    otherwise, label=strrep(name,'_',' ');
end
end

function dimH(x1,x2,y,label)
c=[.28 .28 .28];
plot([x1 x2],[y y],'-','Color',c,'LineWidth',.7);
plot([x1 x1],[y-1 y+1],'-','Color',c);
plot([x2 x2],[y-1 y+1],'-','Color',c);
text((x1+x2)/2,y+.9,label,'HorizontalAlignment','center', ...
    'VerticalAlignment','bottom','FontSize',9,'Color',c);
end

function dimV(x,y1,y2,label)
c=[.28 .28 .28];
plot([x x],[y1 y2],'-','Color',c,'LineWidth',.7);
plot([x-1 x+1],[y1 y1],'-','Color',c);
plot([x-1 x+1],[y2 y2],'-','Color',c);
text(x-.8,(y1+y2)/2,label,'Rotation',90, ...
    'HorizontalAlignment','center','VerticalAlignment','bottom','FontSize',9,'Color',c);
end
