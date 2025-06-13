import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftshift, fftfreq
from scipy.interpolate import interp1d

# Constantes
c =299.792458  # nm/fs
lambda0 = 800  # nm
nu0 = c / lambda0  # THz
omega0 = 2 * np.pi * nu0  # rad/fs ≈ 2π × 374.74 ≈ 2354 rad/fs

# Largeur temporelle de l'impulsion
FWHM_t = 10  # fs
tau = FWHM_t / (2 * np.sqrt(2 * np.log(2)))  # sigma temporel

# Grille temporelle
Nt = 2048
t_max = 200  # fs
t = np.linspace(-t_max, t_max, Nt)
dt = t[1] - t[0]

# Impulsion gaussienne transformée-limitée
E = np.exp(-t**2 / (2 * tau**2)) * np.exp(1j * omega0 * t)

# Retards centrés sur ±75 fs
delays = np.linspace(-75, 75, 500)
frog_trace = np.zeros((len(delays), Nt))

def delay_field(E, delay):
    interp_re = interp1d(t, E.real, kind='linear', bounds_error=False, fill_value=0.0)
    interp_im = interp1d(t, E.imag, kind='linear', bounds_error=False, fill_value=0.0)
    return interp_re(t - delay) + 1j * interp_im(t - delay)

# Calcul de la trace FROG SHG
for i, tau_delay in enumerate(delays):
    E_delayed = delay_field(E, tau_delay)
    signal = E * E_delayed
    spectrum = np.abs(fftshift(fft(signal)))**2
    frog_trace[i, :] = spectrum

# Axe des fréquences angulaires (rad/fs)
omega = fftshift(2 * np.pi * fftfreq(Nt, d=dt))

# Plage utile centrée sur 2ω₀
omega_min = 3  # rad/fs
omega_max = 6  # rad/fs
mask_omega = (omega >= omega_min) & (omega <= omega_max)
omega_crop = omega[mask_omega]
frog_crop = frog_trace[:, mask_omega]

# Affichage
plt.figure(figsize=(3, 3))  # pour correspondre à un format carré
plt.pcolormesh(delays, omega_crop, frog_crop.T, shading='auto', cmap='jet')
plt.xlabel(r'$\tau$ [fs]')
plt.ylabel(r'$\omega$ [rad/fs]')
plt.xlim(-75, 75)
plt.ylim(3, 6)
plt.xticks([-75, 0, 75])
plt.yticks([4, 5, 6])
plt.tight_layout()
plt.show()

