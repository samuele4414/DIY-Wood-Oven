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
%  STAMPA RISULTATI
%  =========================

fprintf('\n--- PIZZA OVEN V0 ---\n');

fprintf('Area piano:        %.4f m^2\n', A_floor);
fprintf('Area trapezio:     %.4f m^2\n', A_trap);
fprintf('Area totale:       %.4f m^2\n', A_total);

fprintf('\nCordierite:\n');
fprintf('Spessore:          %.1f mm\n', t_floor*1000);
fprintf('Volume:            %.5f m^3\n', V_floor);
fprintf('Massa:             %.2f kg\n', m_floor);
fprintf('Capacita termica:  %.0f J/K\n', C_floor);