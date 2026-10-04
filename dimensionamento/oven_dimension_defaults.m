function [p,d] = oven_dimension_defaults()
%OVEN_DIMENSION_DEFAULTS Candidato geometrico, non dimensionamento certificato.
here=fileparts(mfilename('fullpath'));
addpath(fullfile(here,'..','model_v3'));
p=oven_defaults();
p.geom.rearDepth=.25;
p.geom.height=.28;
p.geom.rise=.09;
p.geom.mouthWidth=.72;
p.geom.mouthHeight=.16;
p.geom.hatchWidth=.30;
p.geom.hatchHeight=.14;
p.flow.chimneyDiameter=.13;
p.flow.chimneyHeight=1.0;
p.sim.bakeSeconds=90;
p.sim.recoverySeconds=90;
d.hoodDepth=.25;
d.hoodWidth=.79;
d.collarDiameter=.19; % ingombro ipotizzato della flangia, non diametro fumi
d.outerPipeDiameter=.15; % ipotesi da sostituire col componente scelto
d.edgeMargin=.03;
d.woodLength=.25; % indicazione dell'utente
d.woodThickness=.07; % ipotesi, sezione reale della legna ancora da misurare
d.woodRowGap=.03;
d.woodFrontClearance=.04;
d.woodRearClearance=.03;
d.woodSideClearance=.03;
d.desiredRows=2;
d.peelWidth=.34; % utensile ipotizzato per pizza da 30 cm
d.peelSideClearance=.005;
d.targetPlateC=450; % riferimento comparativo, non criterio di pizza cotta
d.maxPreheatSeconds=7200;
end
