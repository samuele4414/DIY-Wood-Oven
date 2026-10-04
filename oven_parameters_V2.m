%% PIZZA OVEN - MODEL V0
clear;
clc;

%% =========================
%  GEOMETRIA
%  =========================

% Piano di cottura
W_floor = 0.790;        % m
L_floor = 0.410;        % m

% Zona posteriore di combustione - trapezio
B_trap_front = 0.790;   % m
B_trap_rear  = 0.510;   % m
H_trap       = 0.140;   % m

% Area piano
A_floor = W_floor * L_floor;

% Area trapezio
A_trap = ((B_trap_front + B_trap_rear) / 2) * H_trap;

% Area totale in pianta
A_total = A_floor + A_trap;


%% =========================
%  PIANO IN CORDIERITE
%  =========================

t_floor = 0.010;        % m - partiamo da 10 mm

rho_floor = 2600;       % kg/m^3
cp_floor  = 900;        % J/(kg K)
k_floor   = 2.5;        % W/(m K)

% Volume e massa
V_floor = A_floor * t_floor;
m_floor = rho_floor * V_floor;

% Capacita' termica
C_floor = m_floor * cp_floor;
K_floor = 8;       % W/K


%% =========================
%  AMBIENTE
%  =========================

T_ambient = 25 + 273.15;    % K


%% =========================
%  CONDIZIONI INIZIALI
%  =========================

T_floor_0 = T_ambient;

%% =========================
%  HEATING
%  =========================

Q_heating = 5000;       % W


%% =========================
%  VOLTA IN ACCIAIO
%  =========================

H_camera = 0.250;       % m - altezza interna massima

t_roof = 0.002;         % m - 2 mm acciaio

rho_roof = 7800;        % kg/m^3
cp_roof  = 500;         % J/(kg K)
k_roof   = 45;          % W/(m K)

A_roof = A_floor;

V_roof = A_roof * t_roof;

m_roof = rho_roof * V_roof;

C_roof = m_roof * cp_roof;

T_roof_0 = T_ambient;


%% =========================
%  GAS CALDI IN CAMERA
%  =========================

rho_gas = 1.2;          % kg/m^3 - valore iniziale
cp_gas  = 1100;         % J/(kg K)

V_gas = A_total * H_camera;

m_gas = rho_gas * V_gas;

C_gas = m_gas * cp_gas;

T_gas_0 = T_ambient;

%% SCAMBIO GAS -> VOLTA

h_gas_roof = 15;       % W/(m^2 K) - valore iniziale

%% PERDITE TERMICHE VOLTA

K_roof = 5;       % W/K - valore iniziale

%% SCAMBIO GAS -> PAVIMENTO

h_gas_floor = 20;      % W/(m^2 K) - valore iniziale

%% =========================
%  COMBUSTIONE LEGNA
%  =========================

mdot_wood = 0.00131;        % kg/s - portata iniziale di legna
LHV_wood = 15e6;           % J/kg - potere calorifico inferiore
eta_comb = 0.70;           % rendimento effettivo iniziale

Q_comb = mdot_wood * LHV_wood * eta_comb;

%% =========================
%  IRRAGGIAMENTO VOLTA -> PAVIMENTO
%  =========================

epsilon_roof = 0.8;        % emissivita' iniziale
sigma = 5.670374419e-8;    % W/(m^2 K^4)
A_rad_roof_floor = A_floor;

%% =========================
%  CAMINO
%  =========================

H_chimney = 0.50;       % m - altezza camino
D_chimney = 0.10;       % m - diametro interno

A_chimney = pi * D_chimney^2 / 4;
Cd_chimney = 0.65;
%% =========================
%  TIRAGGIO CAMINO
%  =========================

P_ambient = 101325;       % Pa
R_air = 287;              % J/(kg K)

rho_ambient = P_ambient / (R_air * T_ambient);
g = 9.81;

%% PIZZA
D_pizza = 0.320;
A_pizza = pi * D_pizza^2 / 4;

m_pizza = 0.250;
cp_pizza = 2500;
C_pizza = m_pizza * cp_pizza;

T_pizza_0 = T_ambient;

%% SCAMBIO PIANO -> PIZZA
h_floor_pizza = 150;   % W/(m^2 K)
%% SCAMBIO GAS -> PIZZA
h_gas_pizza = 10;   % W/(m^2 K)

%% IRRAGGIAMENTO VOLTA -> PIZZA
epsilon_pizza = 0.9;
A_rad_roof_pizza = A_pizza;

%% ACQUA NELLA PIZZA
water_fraction = 0.60;
m_water_0 = water_fraction * m_pizza;
L_vap = 2.26e6;       % J/kg

%% EVAPORAZIONE
T_evap = 373.15;    % K

%% VELOCITA' EVAPORAZIONE
k_evap = 1e-5;   % kg/(s K)

%% TARGET OPERATIVO
T_floor_target = 450 + 273.15;


%% =========================
%  STAMPA RISULTATI
%  =========================

fprintf('\n--- PIZZA OVEN V1 ---\n');

fprintf('Area piano:        %.4f m^2\n', A_floor);
fprintf('Area trapezio:     %.4f m^2\n', A_trap);
fprintf('Area totale:       %.4f m^2\n', A_total);

fprintf('\nCordierite:\n');
fprintf('Spessore:          %.1f mm\n', t_floor*1000);
fprintf('Volume:            %.5f m^3\n', V_floor);
fprintf('Massa:             %.2f kg\n', m_floor);
fprintf('Capacita termica:  %.0f J/K\n', C_floor);

fprintf('\nVolta in acciaio:\n');
fprintf('Spessore:          %.1f mm\n', t_roof*1000);
fprintf('Volume:            %.5f m^3\n', V_roof);
fprintf('Massa:             %.2f kg\n', m_roof);
fprintf('Capacita termica:  %.0f J/K\n', C_roof);