%% PIZZA OVEN - MODEL V3
% Compatibilita con il comando di avvio delle versioni precedenti.
% I parametri V3 sono definiti in oven_defaults.m e salvati nel Model Workspace.
% Eseguire questo script ripristina i valori predefiniti e rigenera oven_model.slx.
% Per conservare modifiche manuali al diagramma, salvarne prima una copia.

ovenProjectFolder = fileparts(mfilename('fullpath'));
addpath(ovenProjectFolder);
p = oven_defaults();
build_oven_simulink(p);
