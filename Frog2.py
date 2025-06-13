import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft, fftshift, fftfreq
from scipy.interpolate import interp1d

# Constantes
c = 299.792458  # nm/fs
lambda0 = 800  # nm
nu0 = c / lambda0  # THz
omega0 = 2 * np.pi * nu0  # rad/fs

# Largeur temporelle de l'impulsion (FWHM)
FWHM_t = 10  # fs
tau = FWHM_t / (2 * np.sqrt(2 * np.log(2)))  # écart-type temporel

# Grille temporelle
Nt = 2048
t_max = 90  # fs
t = np.linspace(-t_max, t_max, Nt)
dt = t[1] - t[0]

# Impulsion gaussienne transformée-limitée (sans chirp)
E = np.exp(-t**2 / (2 * tau**2)) * np.exp(1j * omega0 * t)

# Paramètre de chirp quadratique (phi'') en fs^2
phi2 = 200  # fs^2

# Passage au domaine fréquentiel
E_w = fft(E)
omega_grid = 2 * np.pi * fftfreq(Nt, dt)  # rad/fs

# Calcul du décalage fréquentiel par rapport à omega0
delta_omega = omega_grid - omega0

# Application de la phase quadratique (chirp)
phase_chirp = np.exp(-1j * 0.5 * phi2 * delta_omega**2)
E_w_chirp = E_w * phase_chirp

# Retour au domaine temporel
E_chirp = ifft(E_w_chirp)

# Remplacement du champ par le champ chirpé
E = E_chirp

# Retards centrés sur ±75 fs
delays = np.linspace(-75, 75, 300)
frog_trace = np.zeros((len(delays), Nt))

def delay_field(E, delay):
    interp_re = interp1d(t, E.real, kind='linear', bounds_error=False, fill_value=0.0)
    interp_im = interp1d(t, E.imag, kind='linear', bounds_error=False, fill_value=0.0)
    return interp_re(t - delay) + 1j * interp_im(t - delay)

# Calcul de la trace PG-FROG : signal = E * |E_delayed|^2
for i, tau_delay in enumerate(delays):
    E_delayed = delay_field(E, tau_delay)
    signal = E * np.abs(E_delayed)**2
    spectrum = np.abs(fftshift(fft(signal)))**2
    frog_trace[i, :] = spectrum

# Axe des fréquences angulaires (rad/fs)
omega = fftshift(2 * np.pi * fftfreq(Nt, d=dt))

# Plage utile centrée sur 2ω₀ (ajustable selon spectre)
omega_min = 1.5  # rad/fs
omega_max = 3 # rad/fs
mask_omega = (omega >= omega_min) & (omega <= omega_max)
omega_crop = omega[mask_omega]
frog_crop = frog_trace[:, mask_omega]

# Affichage
plt.figure(figsize=(3, 3))
plt.pcolormesh(delays, omega_crop, frog_crop.T, shading='auto', cmap='jet')
plt.xlabel(r'$\tau$ [fs]')
plt.ylabel(r'$\omega$ [rad/fs]')
plt.xlim(-75, 75)
plt.ylim(omega_min, omega_max)
plt.xticks([-75, 0, 75])
plt.yticks(np.arange(np.ceil(omega_min), np.floor(omega_max) + 1))
plt.title('PG-FROG trace avec  $\phi\'\'=200$ fs$^2$')
plt.tight_layout()
plt.show()
