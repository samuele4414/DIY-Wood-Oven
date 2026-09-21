function report = verify_simulink()
%VERIFY_SIMULINK Confronta il medesimo ciclo nei due solutori MATLAB/Simulink.
p = oven_defaults();
p.sim.warmupSeconds = 15;
p.sim.recoverySeconds = 10;
p.sim.outputStep = 1;
p.sim.maxStep = .1; % limita l'errore della sola interpolazione dei log Simulink
path = build_oven_simulink(p);
[~,model] = fileparts(path);
close_system(model,0);
load_system(path);
out = sim(model,'ReturnWorkspaceOutputs','on');
logged = out.get('oven_states');
reference = oven_simulate(p);
% Simulink puo salvare piu campioni coincidenti in corrispondenza degli eventi.
[tt,keep] = unique(logged.time,'last');
yy = logged.signals.values(keep,:);
sampled = interp1(tt,yy,reference.t,'linear');
thermal = reference.g.C>0;
report.maximumTemperatureDifferenceK = max(abs(sampled(:,thermal)-reference.y(:,thermal)),[],'all');
report.maximumWaterDifferenceKg = max(abs(sampled(:,~thermal)-reference.y(:,~thermal)),[],'all');
fprintf('Confronto grezzo: %.5g K, %.5g kg.\n', ...
    report.maximumTemperatureDifferenceK,report.maximumWaterDifferenceKg);
assert(all(isfinite(sampled),'all'),'oven:simulink','Stati Simulink non finiti.');
assert(report.maximumTemperatureDifferenceK<.25,'oven:simulink','Differenza MATLAB/Simulink >0.25 K.');
assert(report.maximumWaterDifferenceKg<1e-5,'oven:simulink','Differenza acqua MATLAB/Simulink >1e-5 kg.');
report.passed = true;
fprintf('MATLAB/Simulink: differenza massima %.5g K e %.5g kg.\n', ...
    report.maximumTemperatureDifferenceK,report.maximumWaterDifferenceKg);
close_system(model,0);
build_oven_simulink(oven_defaults()); % file consegnato con il ciclo completo
end
