function oven_refresh_model(model)
%OVEN_REFRESH_MODEL Ricalcola geometria e indici dai parametri del modello.
ws = get_param(model,'ModelWorkspace');
p = ws.getVariable('ovenV3_p');
g = oven_geometry(p);
ws.assignin('ovenV3_g',g);
set_param([model '/Temperature forno'],'Indices',mat2str([g.idx.gas g.idx.shell g.idx.fixed g.idx.hearth]));
set_param([model '/Temperature dischi'],'Indices',mat2str(g.idx.plate(:)'));
set_param([model '/Temperature pizze'],'Indices',mat2str([g.idx.base(:)' g.idx.top(:)']));
end
