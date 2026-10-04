function h = oven_preheat_target(p,targetPlateC,maxSeconds)
%OVEN_PREHEAT_TARGET Arresto sulla media superiore dei due dischi, senza pizze.
assert(isscalar(targetPlateC) && isreal(targetPlateC) && isfinite(targetPlateC) && ...
 targetPlateC>-273.15 && isscalar(maxSeconds) && isfinite(maxSeconds) && maxSeconds>0, ...
 'oven:preheat','Target e durata massima non validi.');
g=oven_geometry(p);
h.targetPlateC=targetPlateC;
h.timeSeconds=NaN;
if mean(g.y0(g.idx.plate(:)))-273.15>=targetPlateC
 h.t=0; h.y=g.y0'; h.reached=true; h.timeSeconds=0;
else
 opts=odeset('RelTol',p.sim.relTol,'AbsTol',p.sim.absTol, ...
  'MaxStep',p.sim.maxStep,'NonNegative',g.idx.water(:),'Events',@targetEvent);
 [h.t,h.y,te,ye]=ode15s(@(t,y)oven_rhs(t,y,p,g,false),[0 maxSeconds],g.y0,opts);
 h.reached=~isempty(te);
 if h.reached
  h.timeSeconds=te(end);
  % ode15s returns the terminal event in its solution; retain its exact state.
  h.t(end)=te(end); h.y(end,:)=ye(end,:);
 end
end
h.endTimeSeconds=h.t(end);
h.endPlateC=mean(h.y(end,g.idx.plate(:)))-273.15;
[~,h.diagnostics]=oven_rhs(h.t(end),h.y(end,:)',p,g,false);
h.plateC=mean(h.y(:,g.idx.plate(:)),2)-273.15;
h.g=g;
 function [value,isterminal,direction]=targetEvent(~,y)
  value=mean(y(g.idx.plate(:)))-273.15-targetPlateC;
  isterminal=1;
  direction=1;
 end
end
