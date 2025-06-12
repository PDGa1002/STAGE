import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO
import pandas as pd

# ========== Données Cristaux SHG ==========
CRYSTALS = {
    "BBO": {"deff": 2.0, "phase_matching_angle": 22.9},
    "KDP": {"deff": 0.4, "phase_matching_angle": 47.7},
    "LiNbO3": {"deff": 27.0, "phase_matching_angle": 36.0},
    "KTP": {"deff": 3.4, "phase_matching_angle": 0.0},
    "Autre": {"deff": None, "phase_matching_angle": 0.0},
}

# ========== Fonctions physiques ==========
def gaussian_pulse(t, tau, delay=0):
    return np.exp(-(t - delay)**2 / (2 * tau**2))

def chirped_pulse(t, tau, chirp=0.05, delay=0):
    return np.exp(-(t - delay)**2 / (2 * tau**2)) * np.exp(1j * chirp * (t - delay)**2)

def apply_filter(E_freq, freqs, filter_type, cutoff):
    if filter_type == "Passe-bas":
        E_freq[np.abs(freqs) > cutoff] = 0
    elif filter_type == "Passe-haut":
        E_freq[np.abs(freqs) < cutoff] = 0
    return E_freq

def apply_shg_crystal(E_t, deff, length_mm):
    L = length_mm * 1e-3  # mm to meters
    E_shg = deff * E_t**2 * L
    return E_t + E_shg

def export_fig_to_png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return buf

def export_array_to_csv(array, name_x="x", name_y="y", xvals=None):
    if xvals is None:
        xvals = np.arange(array.shape[1])
    df = pd.DataFrame(array, columns=[f"{name_y}_{i}" for i in range(array.shape[1])])
    df.insert(0, name_x, xvals)
    return df.to_csv(index=False).encode()

# ========== Interface Streamlit ==========
st.set_page_config(layout="wide")
st.title("🌀 Simulateur FROG (SHG/PG/XFROG) - Ultra Optique")

# ==== SIDEBAR ====
with st.sidebar:
    st.header("📐 Méthode de mesure")
    method = st.selectbox("Méthode FROG", ["SHG-FROG", "PG-FROG", "XFROG"])

    st.header("⚙️ Impulsion")
    N = st.slider("Échantillons (N)", 256, 2048, 512, step=128)
    t_max = st.slider("Fenêtre temporelle (fs)", 50, 2000, 180)
    tau = st.slider("Durée d’impulsion (tau)", 1.0, 100.0, 20.0)
    delay = st.slider("Décalage (fs)", -100.0, 100.0, 0.0)
    pulse_type = st.selectbox("Forme", ["Gaussienne", "Chirpée"])
    chirp = st.slider("Chirp (si applicable)", 0.0, 0.3, 0.05) if pulse_type == "Chirpée" else 0.0

    st.header("🔧 Composants Optiques")
    delay_add = st.slider("Retard optique additionnel (fs)", -100.0, 100.0, 0.0)
    filter_type = st.selectbox("Filtrage Spectral", ["Aucun", "Passe-bas", "Passe-haut"])
    cutoff = st.slider("Coupure (a.u.)", 0.01, 0.5, 0.2)

    st.header("🧪 Cristal SHG")
    use_crystal = st.checkbox("Activer un cristal non-linéaire")
    crystal_type = st.selectbox("Type de cristal", list(CRYSTALS.keys())) if use_crystal else ""
    if use_crystal:
        if crystal_type == "Autre":
            coeff = st.slider("Coeff. non-linéaire (pm/V)", 0.1, 50.0, 1.0)
        else:
            coeff = CRYSTALS[crystal_type]["deff"]
        length = st.slider("Longueur cristal (mm)", 0.1, 5.0, 1.0)
        st.markdown(f"**d_eff** = {coeff} pm/V")
        st.markdown(f"**Angle de phase matching** ≈ {CRYSTALS[crystal_type]['phase_matching_angle']}°")
    else:
        length = 0.0
        coeff = 0.0

    st.header("🧿 Options d'affichage")
    show_phase = st.checkbox("Afficher la phase temporelle/spectrale")

# ==== Grille temporelle ====
t = np.linspace(-t_max / 2, t_max / 2, N)
dt = t[1] - t[0]
freqs = np.fft.fftshift(np.fft.fftfreq(N, d=dt))

# ==== Génération impulsion ====
if pulse_type == "Gaussienne":
    E_t = gaussian_pulse(t, tau, delay + delay_add)
else:
    E_t = chirped_pulse(t, tau, chirp, delay + delay_add)

# ==== Filtrage Spectral ====
E_freq = np.fft.fftshift(np.fft.fft(E_t))
if filter_type != "Aucun":
    E_freq = apply_filter(E_freq, freqs, filter_type, cutoff)
E_t = np.fft.ifft(np.fft.ifftshift(E_freq))

# ==== Cristal SHG ====
if use_crystal:
    E_t = apply_shg_crystal(E_t, coeff, length)

# ==== Génération de la gate pour XFROG ====
reference_pulse = gaussian_pulse(t, tau / 2)

# ==== Calcul FROG ====
frog_trace = np.zeros((N, N))
for i, delay_val in enumerate(t):
    shift = i - N // 2
    if method == "PG-FROG":
        gate = np.roll(np.abs(E_t)**2, shift)
    elif method == "SHG-FROG":
        gate = np.roll(E_t, shift)
    elif method == "XFROG":
        gate = np.roll(reference_pulse, shift)
    signal = E_t * gate
    spectrum = np.fft.fftshift(np.fft.fft(signal))
    frog_trace[:, i] = np.abs(spectrum)**2

# ========== AFFICHAGE ========== 
col1, col2 = st.columns(2)

# --- Affichage temporel & spectral ---
with col1:
    st.subheader("🕒 Impulsion et Spectre")
    fig1, ax = plt.subplots(2, 2, figsize=(10, 6))
    ax[0, 0].plot(t, np.abs(E_t)**2, label="Intensité", color='blue')
    ax[0, 0].set_title("Intensité temporelle")
    if show_phase:
        ax[0, 0].twinx().plot(t, np.angle(E_t), label="Phase", color='red', linestyle='dotted')

    ax[0, 1].plot(freqs, np.abs(E_freq)**2, label="Spectre", color='green')
    ax[0, 1].set_title("Spectre")
    if show_phase:
        ax[0, 1].twinx().plot(freqs, np.angle(E_freq), label="Phase", color='purple', linestyle='dotted')

    ax[1, 0].axis("off")
    ax[1, 1].axis("off")
    st.pyplot(fig1)

# --- Affichage trace FROG ---
with col2:
    st.subheader(f"📊 Trace {method}")
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    extent = [t[0], t[-1], freqs[0], freqs[-1]]
    im = ax2.imshow(frog_trace, extent=extent, origin='lower', aspect='auto', cmap='inferno')
    ax2.set_xlabel("Retard (fs)")
    ax2.set_ylabel("Fréquence (a.u.)")
    ax2.set_title(f"{method} Trace")
    fig2.colorbar(im, ax=ax2, label="Intensité")
    st.pyplot(fig2)

    png_buf = export_fig_to_png(fig2)
    st.download_button("📥 Télécharger l’image", data=png_buf, file_name=f"{method.lower()}_trace.png", mime="image/png")
    st.download_button("⬇️ Exporter données XFROG", data=export_array_to_csv(frog_trace, "Temps", "Intensité", t), file_name=f"{method.lower()}_data.csv", mime="text/csv")








