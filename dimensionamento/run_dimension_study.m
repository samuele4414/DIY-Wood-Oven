function study = run_dimension_study(outputDir)
%RUN_DIMENSION_STUDY Sensibilita' una variabile alla volta, a target comune.
% La cappa esterna non entra nei bilanci V3; nessuna graduatoria di ottimo.
here=fileparts(mfilename('fullpath'));
if nargin==0, outputDir=fullfile(here,'results'); end
if ~exist(outputDir,'dir'), mkdir(outputDir); end
[p,d]=oven_dimension_defaults();
study.p=p; study.d=d; study.g=oven_dimension_geometry(p,d);
study.names={'candidato_25cm','focolare_14cm','focolare_20cm','focolare_30cm', ...
 'volta_25cm','volta_30cm','bocca_alta_14cm','bocca_larga_60cm', ...
 'camino_diametro_15cm','camino_altezza_50cm','volta_refrattaria', ...
 'legna_4_5kg_h','legna_4_5kg_h_pietra_20mm'};
n=numel(study.names);
study.parameters=repmat({p},1,n);
study.parameters{2}.geom.rearDepth=.14;
study.parameters{3}.geom.rearDepth=.20;
study.parameters{4}.geom.rearDepth=.30;
study.parameters{5}.geom.height=.25; study.parameters{5}.geom.rise=.06;
study.parameters{6}.geom.height=.30; study.parameters{6}.geom.rise=.11;
study.parameters{7}.geom.mouthHeight=.14;
study.parameters{8}.geom.mouthWidth=.60;
study.parameters{9}.flow.chimneyDiameter=.15;
study.parameters{10}.flow.chimneyHeight=.50;
study.parameters{11}.roof.material='refractory';
study.parameters{12}.fuel.kgH=4.5;
study.parameters{13}.fuel.kgH=4.5; study.parameters{13}.floor.thickness=.020;
study.results=cell(1,n); study.preheat=cell(1,n); study.geometries=cell(1,n);
for j=1:n
 pp=study.parameters{j};
 study.geometries{j}=oven_dimension_geometry(pp,d);
 fprintf('Dimensioni %d/%d: %s; target %.0f C, massimo %.0f min.\n', ...
  j,n,study.names{j},d.targetPlateC,d.maxPreheatSeconds/60);
 h=oven_preheat_target(pp,d.targetPlateC,d.maxPreheatSeconds);
 study.preheat{j}=h;
 row=struct('name',string(study.names{j}),'reached',h.reached, ...
  'preheatMinutes',h.timeSeconds/60,'preheatEndMinutes',h.endTimeSeconds/60, ...
  'endPreheatPlateC',h.endPlateC,'plateC_atLoad',NaN,'lowerPlateC_atLoad',NaN, ...
  'shellFrontC_atLoad',NaN,'gasFrontC_atLoad',NaN,'gasRearC_atLoad',NaN, ...
  'draftPa_atLoad',NaN,'massFlowKgS_atLoad',NaN,'dropUpperPlateBakeK',NaN, ...
  'water90g_perPizza',NaN,'base90C',NaN,'top90C',NaN,'maxEnergyResidualW',NaN, ...
  'rearDepthCm',100*pp.geom.rearDepth,'roofHeightCm',100*pp.geom.height, ...
  'mouthWidthCm',100*pp.geom.mouthWidth,'mouthHeightCm',100*pp.geom.mouthHeight, ...
  'flueDiameterCm',100*pp.flow.chimneyDiameter,'flueHeightM',pp.flow.chimneyHeight, ...
  'roofMaterial',string(pp.roof.material),'woodKgH',pp.fuel.kgH, ...
  'stoneThicknessMm',pp.floor.thickness*1000);
 if h.reached
  pp.sim.warmupSeconds=h.timeSeconds;
  r=oven_simulate(pp);
  study.parameters{j}=pp;
  study.results{j}=r;
  loadState=r.metrics.atLoad;
  row.plateC_atLoad=mean(loadState.plateMeanC);
  row.lowerPlateC_atLoad=mean(loadState.plateBottomMeanC);
  row.shellFrontC_atLoad=loadState.shellC(1);
  row.gasFrontC_atLoad=loadState.gasC(1);
  row.gasRearC_atLoad=loadState.gasC(2);
  row.draftPa_atLoad=interp1(r.t,r.diagnostics.draftPa,h.timeSeconds);
  row.massFlowKgS_atLoad=interp1(r.t,r.diagnostics.massFlow,h.timeSeconds);
  bake=r.t>=h.timeSeconds & r.t<=h.timeSeconds+pp.sim.bakeSeconds;
  plateTrace=mean(r.y(bake,r.g.idx.plate(:)),2)-273.15;
  row.dropUpperPlateBakeK=row.plateC_atLoad-min(plateTrace);
  row.water90g_perPizza=1000*mean(r.metrics.at90.waterKg);
  row.base90C=mean(r.metrics.at90.baseMeanC);
  row.top90C=mean(r.metrics.at90.topMeanC);
  row.maxEnergyResidualW=r.metrics.maxEnergyResidualW;
  fprintf('  Target raggiunto in %.2f min; carico a %.2f C.\n', ...
   row.preheatMinutes,row.plateC_atLoad);
 else
  fprintf('  Target non raggiunto: %.2f C dopo %.0f min; cottura non simulata.\n', ...
   h.endPlateC,h.endTimeSeconds/60);
 end
 if j==1, rows=row; else, rows(j)=row; end
end
study.rows=struct2table(rows);
study.flags={'Dimensionamento preliminare: nessuna calibrazione sperimentale senza misure.', ...
 'Confronti a pari media superficiale dei dischi; volta e gas possono differire.', ...
 '450 C e'' solo un riferimento comparativo, non ottimo o criterio di cottura.', ...
 'Coefficienti di scambio, combustione e distribuzione spaziale incerti e mantenuti fissi.', ...
 'La variazione altezza volta mantiene imposta a 19 cm cambiando la freccia.', ...
 'Il caso pietra 20 mm va confrontato con legna 4.5 kg/h, non con la base a 3.5 kg/h.', ...
 'Cappa esterna non modellata: risultati non verificano posizione o cattura dei fumi.', ...
 'Acqua e temperature pizza a 90 s sono indicatori del modello, non cottura validata.'};
save(fullfile(outputDir,'study.mat'),'study');
writetable(study.rows,fullfile(outputDir,'summary.csv'));
fprintf('Confronto salvato in %s\n',outputDir);
end
