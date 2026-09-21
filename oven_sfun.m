function oven_sfun(block)
%OVEN_SFUN Adattatore continuo: usa esattamente il bilancio MATLAB V3.
block.NumDialogPrms = 2; % p, geometria derivata g
g = block.DialogPrm(2).Data;
block.NumInputPorts = 1;
block.NumOutputPorts = 1;
block.SetPreCompPortInfoToDefaults;
block.InputPort(1).Dimensions = 1;
block.InputPort(1).DatatypeID = 0;
block.InputPort(1).Complexity = 'Real';
block.InputPort(1).DirectFeedthrough = false;
block.OutputPort(1).Dimensions = numel(g.C);
block.OutputPort(1).DatatypeID = 0;
block.OutputPort(1).Complexity = 'Real';
block.NumContStates = numel(g.C);
block.SampleTimes = [0 0];
block.SimStateCompliance = 'DefaultSimState';
block.RegBlockMethod('InitializeConditions', @initialize);
block.RegBlockMethod('Outputs', @outputs);
block.RegBlockMethod('Derivatives', @derivatives);
end

function initialize(block)
g = block.DialogPrm(2).Data;
block.ContStates.Data = g.y0;
end

function outputs(block)
block.OutputPort(1).Data = block.ContStates.Data;
end

function derivatives(block)
p = block.DialogPrm(1).Data;
g = block.DialogPrm(2).Data;
block.Derivatives.Data = oven_rhs(block.CurrentTime, ...
    block.ContStates.Data,p,g,block.InputPort(1).Data > .5);
end
