import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Fonction de transmission Z-scan
def compute_transmission(z, w0, zR, n2, I0, open_aperture=False, beta=0):
    wz = w0 * np.sqrt(1 + (z / zR)**2)
    Iz = I0 / wz**2
    if open_aperture:
        return 1 - beta * Iz  # absorption non linéaire (ex: Z-scan ouvert)
    else:
        return 1 - n2 * Iz * (z / zR) / (1 + (z / zR)**2)  # effet Kerr (Z-scan fermé)

# Profil gaussien 3D
def gaussian_beam_profile(w0, zR, z_range, r_range):
    Z, R = np.meshgrid(z_range, r_range)
    wz = w0 * np.sqrt(1 + (Z / zR)**2)
    intensity = np.exp(-2 * (R**2) / wz**2)
    return Z, R, intensity

# Configuration de la page
st.set_page_config(layout="wide")
st.title("Simulation Z-scan optique interactive")
st.markdown("**Par : Conversion de l'interface Tkinter en Streamlit**")

# Colonnes
col1, col2, col3 = st.columns([1, 2, 2])

# Colonne gauche : paramètres
with col1:
    st.header("Paramètres")
    n2 = st.slider("n2 (indice non linéaire)", min_value=1e-5, max_value=1e-3, value=1e-4, step=1e-5, format="%.1e")
    w0 = st.slider("w0 (rayon au foyer)", min_value=0.2, max_value=5.0, value=1.0, step=0.1)
    I0 = st.slider("I0 (intensité)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    open_aperture = st.checkbox("Z-scan ouvert (transmission ouverte)")
    beta = 0
    if open_aperture:
        beta = st.slider("β (absorption non linéaire)", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

# Données de base
z = np.linspace(-30, 30, 300)
r = np.linspace(0, 5, 100)
zR = 10  # Longueur de Rayleigh

# Calculs
trans = compute_transmission(z, w0, zR, n2, I0, open_aperture, beta)
Z, R, I = gaussian_beam_profile(w0, zR, z, r)

# Colonne centrale : transmission
with col2:
    st.subheader("Transmission Z-scan")

    fig1, ax1 = plt.subplots(figsize=(5, 4))
    ax1.plot(z, trans, label="Transmission", color='blue')
    ax1.set_xlabel("z (mm)")
    ax1.set_ylabel("Transmission")

    # Centrage vertical automatique
    ymin = min(trans) - 0.01
    ymax = max(trans) + 0.01
    ax1.set_ylim(ymin, ymax)

    ax1.grid(True)
    fig1.tight_layout()

    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.pyplot(fig1)
    st.markdown("</div>", unsafe_allow_html=True)

# Colonne droite : profil gaussien 3D + trace
with col3:
    st.subheader("Profil Gaussien 3D du faisceau")

    fig2 = plt.figure(figsize=(8, 6))
    ax2 = fig2.add_subplot(111, projection='3d')
    surf = ax2.plot_surface(Z, R, I, cmap='inferno')
    ax2.set_xlabel("z (mm)")
    ax2.set_ylabel("r (mm)")
    ax2.set_zlabel("Intensité")
    fig2.colorbar(surf, ax=ax2, shrink=0.5, aspect=10, label="Intensité")
    st.pyplot(fig2)

    st.subheader("Trace du faisceau sur le détecteur (z = 0)")

    # Profil transverse à z = 0
    r_2d = np.linspace(-5, 5, 200)
    x, y = np.meshgrid(r_2d, r_2d)
    r_sq = x**2 + y**2
    w = w0  # wz = w0 à z = 0
    intensity_2d = np.exp(-2 * r_sq / w**2)

    fig3, ax3 = plt.subplots()
    im = ax3.imshow(intensity_2d, extent=[-5, 5, -5, 5], cmap='inferno')
    ax3.set_xlabel("x (mm)")
    ax3.set_ylabel("y (mm)")
    ax3.set_title("Profil transverse du faisceau")
    fig3.colorbar(im, ax=ax3, label="Intensité")
    st.pyplot(fig3)
