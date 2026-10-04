function s = run_compact_front_study()
%RUN_COMPACT_FRONT_STUDY Confronto geometrico, senza riutilizzare previsioni V3.
[p,d]=oven_dimension_defaults();
c.frontDepth=.08; % proposta: 8 cm dalla porta al bordo iniziale del piano
c.flueY=.045;    % asse camino 4.5 cm dentro la proiezione del piano
g=oven_compact_front_geometry(p,d,c);
s=struct('p',p,'d',d,'c',c,'g',g);
assert(abs(g.overallDepth-.74)<1e-12);
assert(max(abs(g.doorToPlateNear-.125))<1e-12);
assert(max(abs(g.doorToPlateCenter-.285))<1e-12);
assert(abs(g.doorToFlueAxis-.125)<1e-12);
assert(max(abs(g.collarY-[-.05 .14]))<1e-12);
assert(abs(g.collarFrontMargin-.03)<1e-12 && ~g.internalLintel);
% Un tubo spostato troppo avanti deve essere rifiutato.
bad=c; bad.flueY=0; rejected=false;
try
    oven_compact_front_geometry(p,d,bad);
catch err
    rejected=strcmp(err.identifier,'oven:compact');
end
assert(rejected,'Raccordo in collisione col fronte non rifiutato.');
s.validation='7 verifiche geometriche superate; nessuna validazione fluidodinamica.';
out=fullfile(fileparts(mfilename('fullpath')),'results');
if ~exist(out,'dir'), mkdir(out); end
save(fullfile(out,'fronte_compatto.mat'),'s');
drawComparison(s,out);
drawPlan(s,out);
fprintf('%s\n',s.validation);
fprintf('Profondita %.1f cm; porta-disco %.1f cm; porta-asse camino %.1f cm.\n', ...
    100*g.overallDepth,100*g.doorToPlateNear(1),100*g.doorToFlueAxis);
end

function drawComparison(s,out)
p=s.p; d=s.d; g=s.g;
fig=figure('Visible','off','Theme','light','Color','w','Scrollable','off', ...
    'Position',[50 50 1250 940]);
guard=onCleanup(@()close(fig));
tiledlayout(2,1,'TileSpacing','loose','Padding','loose');
for compact=0:1
    nexttile; hold on;
    if compact
        front=100*s.c.frontDepth; axisX=100*g.doorToFlueAxis;
        near=100*g.doorToPlateNear(1);
        heading='Variante compatta — raccolta in alto, vano continuo';
    else
        front=100*d.hoodDepth; axisX=100*g.reference.doorToFlueAxis;
        near=100*g.reference.frontedgeToPlateNear(1);
        heading='Precedente — raccolta in un tratto separato davanti al piano';
    end
    L=100*p.geom.frontDepth; R=100*p.geom.rearDepth;
    total=front+L+R; z=100*p.geom.height; mh=100*p.geom.mouthHeight;
    blue=[.18 .35 .45]; purple=[.4 .2 .55]; grey=[.3 .35 .4];
    patch([0 front front 0],[0 0 -1 -1],[.86 .92 .96],'EdgeColor',grey);
    patch(front+[0 L L 0],[0 0 -1 -1],[.94 .88 .72],'EdgeColor',grey);
    patch(front+L+[0 R R 0],[0 0 -1 -1],[.97 .78 .58],'EdgeColor',grey);
    rr=50*p.flow.chimneyDiameter;
    plot([0 axisX-rr],[z z],'Color',grey,'LineWidth',2);
    plot([axisX+rr total total],[z z 0],'Color',grey,'LineWidth',2);
    plot([0 0],[mh z],'Color',grey,'LineWidth',2);
    plot([0 0],[0 mh],'Color',purple,'LineWidth',5);
    plot([axisX-rr axisX-rr],[z z+13],'Color',blue,'LineWidth',2);
    plot([axisX+rr axisX+rr],[z z+13],'Color',blue,'LineWidth',2);
    plot(axisX+[-1 1]*50*d.collarDiameter,[z+.6 z+.6], ...
        '--','Color',blue,'LineWidth',2);
    if ~compact
        plot([front front],[mh z],'Color',grey,'LineWidth',2);
    else
        plot([front front],[0 z],':','Color',[.7 .7 .7]);
    end
    plot(near+[0 100*p.geom.plateDiameter],[.7 .7],'Color',blue,'LineWidth',4);
    text(near+16,4,'Dischi in proiezione','HorizontalAlignment','center','FontSize',10);
    text(-3,8,'Porta','Rotation',90,'HorizontalAlignment','center','Color',purple);
    for k=1:size(g.reference.woodRows,1)
        yy=front+100*g.reference.woodRows(k,3:4);
        patch([yy(1) yy(2) yy(2) yy(1)],[0 0 7 7],[.6 .34 .16]);
    end
    text(front+L+R/2,11,'Legna','HorizontalAlignment','center','FontSize',10);
    if compact, flowZ=20; else, flowZ=10; end
    quiver(front+L*.68,flowZ,axisX-(front+L*.68),0,0, ...
        'Color',[.75 .35 .08],'LineWidth',1.5,'MaxHeadSize',.25);
    quiver(axisX,flowZ,0,z+9-flowZ,0, ...
        'Color',[.75 .35 .08],'LineWidth',1.5,'MaxHeadSize',.3);
    text(34,z+7,'Raccordo sul tetto Ø19 cm; tubo interno Ø13 cm', ...
        'Color',blue,'FontSize',10);
    text(34,z+3,'Ipotesi di ingombro; adattatore e flusso da verificare', ...
        'FontSize',9,'Color',grey);
    plot([axisX+9 32],[z+1 z+6],'--','Color',blue);
    dimension(0,front,-5,sprintf('%.0f',front));
    dimension(front,front+L,-5,'Piano 41');
    dimension(front+L,total,-5,'Focolare 25');
    dimension(0,near,-12,sprintf('Porta–disco %.1f',near));
    text(45,-12,sprintf('Profondita totale %.0f cm',total),'FontWeight','bold','FontSize',11);
    axis equal; xlim([-8 100]); ylim([-16 47]); axis off;
    title({heading;'Quote interne in cm — frecce schematiche, non simulazione dei fumi'},'FontSize',12);
end
exportgraphics(fig,fullfile(out,'confronto_frontale_compatto.png'),'Resolution',150);
end

function drawPlan(s,out)
p=s.p; d=s.d; g=s.g;
W=100*p.geom.width; L=100*p.geom.frontDepth; R=100*p.geom.rearWidth;
F=100*p.geom.rearDepth; H=100*s.c.frontDepth;
fig=figure('Visible','off','Theme','light','Color','w','Scrollable','off', ...
    'Position',[60 60 1000 960]);
guard=onCleanup(@()close(fig));
ax=axes(fig,'Position',[.1 .1 .8 .8]); hold(ax,'on');
patch([0 W W 0],[-H -H 0 0],[.87 .92 .96]);
patch([0 W W 0],[0 0 L L],[.94 .88 .72]);
patch([0 W (W+R)/2 (W-R)/2],[L L L+F L+F],[.97 .78 .58]);
t=linspace(0,2*pi,200);
for k=1:2
    cc=100*p.geom.plateCenters(k,:); r=50*p.geom.plateDiameter;
    patch(cc(1)+r*cos(t),cc(2)+r*sin(t),[.71 .83 .89],'EdgeColor',[.18 .35 .45]);
    text(cc(1),cc(2),sprintf('Disco %d\nØ32 cm',k),'HorizontalAlignment','center','FontSize',12);
end
for k=1:size(g.reference.woodRows,1)
    b=100*g.reference.woodRows(k,:);
    patch([b(1) b(2) b(2) b(1)],[b(3) b(3) b(4) b(4)],[.6 .34 .16]);
    text(mean(b(1:2)),mean(b(3:4)),'Legna 25 cm','Color','w','HorizontalAlignment','center');
end
fc=100*g.flueCenter;
plot(fc(1)+50*d.collarDiameter*cos(t),fc(2)+50*d.collarDiameter*sin(t), ...
    '--','Color',[.42 .2 .55],'LineWidth',2);
plot(fc(1)+50*p.flow.chimneyDiameter*cos(t),fc(2)+50*p.flow.chimneyDiameter*sin(t), ...
    ':','Color',[.42 .2 .55],'LineWidth',2);
plot(fc(1),fc(2),'+','Color',[.42 .2 .55]);
text(W+4,fc(2)+6,{'Camino sul tetto';'proiettato in pianta';'NON foro nel piano'},'FontSize',10);
plot([fc(1)+9 W+3],[fc(2) fc(2)+5],'--','Color',[.42 .2 .55]);
mx=(W+[-1 1]*100*p.geom.mouthWidth)/2;
plot(mx,[-H -H],'Color',[.42 .2 .55],'LineWidth',4);
text(W/2,-H-3,'Porta frontale 72 × 16 cm','HorizontalAlignment','center','FontSize',11);
text(W/2,L+F+4,'Pianta interna 79 × 74 cm (inviluppo)','HorizontalAlignment','center','FontSize',12);
text(-4,-H/2,'8 cm','HorizontalAlignment','right','FontSize',10);
text(-4,L/2,'41 cm','HorizontalAlignment','right','FontSize',10);
text(-4,L+F/2,'25 cm','HorizontalAlignment','right','FontSize',10);
axis equal; xlim([-14 W+31]); ylim([-H-9 L+F+9]); axis off;
title({'Variante compatta — il raccordo occupa il tetto';'Piano 79 × 41 cm e dischi invariati'},'FontSize',13);
exportgraphics(fig,fullfile(out,'pianta_frontale_compatto.png'),'Resolution',150);
end

function dimension(a,b,z,label)
plot([a b],[z z],'Color',[.4 .4 .4]);
plot([a a],[z-1 z+1],'Color',[.4 .4 .4]);
plot([b b],[z-1 z+1],'Color',[.4 .4 .4]);
text((a+b)/2,z+.6,label,'HorizontalAlignment','center','VerticalAlignment','bottom','FontSize',10);
end
