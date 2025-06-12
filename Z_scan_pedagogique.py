import pygame
import pygame_gui
import math

pygame.init()

WIDTH, HEIGHT = 1200, 600
FPS = 60
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (100, 100, 255)
BLACK = (0, 0, 0)
LENS_COLOR = (0, 200, 255)
CRYSTAL_COLOR = (0, 255, 200)
DIAPHRAGM_COLOR = (200, 200, 200)
PHOTODIODE_COLOR = (255, 255, 0)
BEAMSPLITTER_COLOR = (0, 255, 0)  # Vert


non_linear_strength = 3.0
shg_threshold = 2.0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulation Optique avec GUI")
clock = pygame.time.Clock()

manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# UI Elements positions for bottom left area
base_x = 20
base_y = HEIGHT - 130

nl_slider = pygame_gui.elements.UIHorizontalSlider(
    pygame.Rect((base_x, base_y), (180, 30)),
    start_value=non_linear_strength,
    value_range=(0, 10),
    manager=manager
)
nl_label = pygame_gui.elements.UILabel(
    pygame.Rect((base_x, base_y - 25), (180, 25)),
    "Non-linéarité",
    manager
)

shg_slider = pygame_gui.elements.UIHorizontalSlider(
    pygame.Rect((base_x + 200, base_y), (180, 30)),
    start_value=shg_threshold,
    value_range=(0.1, 5),
    manager=manager
)
shg_label = pygame_gui.elements.UILabel(
    pygame.Rect((base_x + 200, base_y - 25), (180, 25)),
    "Seuil SHG",
    manager
)

reset_button = pygame_gui.elements.UIButton(
    pygame.Rect((base_x + 410, base_y), (120, 40)),
    "Reset",
    manager
)

crystal_slider = pygame_gui.elements.UIHorizontalSlider(
    pygame.Rect((base_x + 550, base_y), (180, 30)),
    start_value=50,
    value_range=(20, 200),
    manager=manager
)
crystal_label = pygame_gui.elements.UILabel(
    pygame.Rect((base_x + 550, base_y - 25), (180, 25)),
    "Hauteur Cristal",
    manager
)

# Graphe transmission
graph_x = 20
graph_y = HEIGHT - 120
graph_w = 600
graph_h = 100

# Labels numériques taux de transmission pour 3 photodiodes
transmission_label_bottom = pygame_gui.elements.UILabel(
    pygame.Rect((graph_x + graph_w + 10, graph_y + graph_h // 2 - 40), (220, 25)),
    "Transmission bas: 0%",
    manager
)
transmission_label_top = pygame_gui.elements.UILabel(
    pygame.Rect((graph_x + graph_w + 10, graph_y + graph_h // 2 - 10), (220, 25)),
    "Transmission haut 1: 0%",
    manager
)
transmission_label_top2 = pygame_gui.elements.UILabel(
    pygame.Rect((graph_x + graph_w + 10, graph_y + graph_h // 2 + 20), (220, 25)),
    "Transmission haut 2: 0%",
    manager
)

# Optique setup
lens_x, lens_y = WIDTH // 2, HEIGHT // 2
lens_height = 200
focal_length = 150

crystal_x = lens_x + 200
crystal_width = 20
crystal_y = lens_y
crystal_height = 100

laser_origin = (100, HEIGHT // 2)
diaphragm_enabled = False
diaphragm_aperture = 60
diaphragm_x = crystal_x + 100

photodiode_bottom_x = diaphragm_x + 30
photodiode_bottom_y = lens_y

# Photodiode haute sur trajectoire réfléchie par la lame séparatrice principale
beamsplitter_x = lens_x - 100
beamsplitter_y = lens_y

photodiode_top_x = beamsplitter_x + 0
photodiode_top_y = beamsplitter_y - 100

photodiode_radius = 15

# Deuxième lame séparatrice
beamsplitter2_x = crystal_x + 50
beamsplitter2_y = lens_y

# Photodiode haute 2 sur trajectoire réfléchie par la deuxième lame séparatrice
photodiode_top2_x = beamsplitter2_x + 0
photodiode_top2_y = beamsplitter2_y - 100

class LightPulse:
    def __init__(self, x, y, angle, color=RED):
        self.x = x
        self.y = y
        self.angle = angle
        self.color = color
        self.speed = 5
        self.length = 10
        self.passed_lens = False
        self.passed_crystal = False
        self.passed_beamsplitter = False
        self.passed_beamsplitter2 = False
        self.alive = True
        self.intensity = max(1.0, 1.0 + abs(y - lens_y) / 50)
        self.transmitted = False
        self.detected_by_photodiode_bottom = False
        self.detected_by_photodiode_top = False
        self.detected_by_photodiode_top2 = False

    def update(self):
        if not self.alive:
            return

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Passage lame séparatrice principale
        if not self.passed_beamsplitter and self.x >= beamsplitter_x:
            self.passed_beamsplitter = True
            if abs(self.y - beamsplitter_y) < 5:
                # Réfléchie vers le haut
                reflected_pulse = LightPulse(self.x, self.y, -math.pi / 2, self.color)
                pulses.append(reflected_pulse)
                # Transmission continue à droite

        # Passage lame séparatrice secondaire
        if not self.passed_beamsplitter2 and self.x >= beamsplitter2_x:
            self.passed_beamsplitter2 = True
            if abs(self.y - beamsplitter2_y) < 5:
                # Réflexion vers le haut
                reflected_pulse = LightPulse(self.x, self.y, -math.pi / 2, self.color)
                pulses.append(reflected_pulse)
                # Transmission vers le bas continue en angle -pi/2
                self.angle = -math.pi / 2

        # Passage lentille
        if not self.passed_lens and self.x >= lens_x:
            focal_point = (lens_x + focal_length, lens_y)
            self.angle = math.atan2(focal_point[1] - self.y, focal_point[0] - lens_x)
            self.passed_lens = True

        # Passage cristal
        if not self.passed_crystal and crystal_x <= self.x <= crystal_x + crystal_width:
            angle_change = math.radians(non_linear_strength * self.intensity)
            self.angle += angle_change
            if self.intensity > shg_threshold:
                self.color = BLUE
            self.passed_crystal = True

        # Passage diaphragme
        if diaphragm_enabled and self.x >= diaphragm_x:
            if abs(self.y - lens_y) > diaphragm_aperture // 2:
                self.alive = False

        # Détection photodiode basse
        if not self.detected_by_photodiode_bottom and self.x >= photodiode_bottom_x:
            dist_bottom = math.hypot(self.x - photodiode_bottom_x, self.y - photodiode_bottom_y)
            if dist_bottom <= photodiode_radius:
                self.detected_by_photodiode_bottom = True

        # Détection photodiode haute 1 (première lame séparatrice)
        if not self.detected_by_photodiode_top:
            dist_top = math.hypot(self.x - photodiode_top_x, self.y - photodiode_top_y)
            if dist_top <= photodiode_radius and math.isclose(self.angle, -math.pi / 2, abs_tol=0.1):
                self.detected_by_photodiode_top = True

        # Détection photodiode haute 2 (deuxième lame séparatrice)
        if not self.detected_by_photodiode_top2:
            dist_top2 = math.hypot(self.x - photodiode_top2_x, self.y - photodiode_top2_y)
            if dist_top2 <= photodiode_radius and math.isclose(self.angle, -math.pi / 2, abs_tol=0.1):
                self.detected_by_photodiode_top2 = True

        if self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.transmitted = True

    def draw(self, surface):
        if not self.alive:
            return
        end_x = self.x + math.cos(self.angle) * self.length
        end_y = self.y + math.sin(self.angle) * self.length
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), 2)

    def is_off_screen(self):
        return self.x > WIDTH or self.y < 0 or self.y > HEIGHT or not self.alive

pulses = []
frame_counter = 0
transmission_history_bottom = []
transmission_history_top = []
transmission_history_top2 = []

def emit_pulses():
    global frame_counter
    frame_counter += 1
    if frame_counter % 10 == 0:
        for i in range(-2, 3):
            pulses.append(LightPulse(laser_origin[0], laser_origin[1] + i * 10, 0))

def draw_lens():
    pygame.draw.line(screen, LENS_COLOR, (lens_x, lens_y - lens_height // 2), (lens_x, lens_y + lens_height // 2), 5)

def draw_crystal():
    pygame.draw.rect(screen, CRYSTAL_COLOR, (crystal_x, crystal_y - crystal_height // 2, crystal_width, crystal_height))

def draw_diaphragm():
    if diaphragm_enabled:
        pygame.draw.rect(screen, DIAPHRAGM_COLOR, (diaphragm_x - 5, 0, 10, lens_y - diaphragm_aperture // 2))
        pygame.draw.rect(screen, DIAPHRAGM_COLOR, (diaphragm_x - 5, lens_y + diaphragm_aperture // 2, 10, HEIGHT))

def draw_beamsplitters():
    # Lame séparatrice principale
    pygame.draw.line(screen, BEAMSPLITTER_COLOR, (beamsplitter_x - 20, beamsplitter_y + 20), (beamsplitter_x + 20, beamsplitter_y - 20), 3)
    # Lame séparatrice secondaire
    pygame.draw.line(screen, BEAMSPLITTER_COLOR, (beamsplitter2_x -20, beamsplitter2_y + 20), (beamsplitter2_x + 20, beamsplitter2_y -20), 3)

def draw_photodiodes():
    # Photodiode basse
    pygame.draw.circle(screen, PHOTODIODE_COLOR, (photodiode_bottom_x, photodiode_bottom_y), photodiode_radius)
    pygame.draw.circle(screen, BLACK, (photodiode_bottom_x, photodiode_bottom_y), photodiode_radius, 2)

    # Photodiode haute 1
    pygame.draw.circle(screen, PHOTODIODE_COLOR, (photodiode_top_x, photodiode_top_y), photodiode_radius)
    pygame.draw.circle(screen, BLACK, (photodiode_top_x, photodiode_top_y), photodiode_radius, 2)

    # Photodiode haute 2
    pygame.draw.circle(screen, PHOTODIODE_COLOR, (photodiode_top2_x, photodiode_top2_y), photodiode_radius)
    pygame.draw.circle(screen, BLACK, (photodiode_top2_x, photodiode_top2_y), photodiode_radius, 2)

def draw_transmission_graph():
    max_len = 100

    detected_bottom = sum(1 for p in pulses if p.detected_by_photodiode_bottom)
    detected_top = sum(1 for p in pulses if p.detected_by_photodiode_top)
    detected_top2 = sum(1 for p in pulses if p.detected_by_photodiode_top2)
    total = len(pulses)

    transmission_bottom = detected_bottom / total if total > 0 else 0
    transmission_top = detected_top / total if total > 0 else 0
    transmission_top2 = detected_top2 / total if total > 0 else 0

    transmission_history_bottom.append(transmission_bottom)
    transmission_history_top.append(transmission_top)
    transmission_history_top2.append(transmission_top2)

    if len(transmission_history_bottom) > max_len:
        transmission_history_bottom.pop(0)
    if len(transmission_history_top) > max_len:
        transmission_history_top.pop(0)
    if len(transmission_history_top2) > max_len:
        transmission_history_top2.pop(0)

    # Fond graph
    pygame.draw.rect(screen, (50, 50, 50), (graph_x, graph_y, graph_w, graph_h))

    # Dessin des courbes
    def draw_curve(history, color):
        if len(history) < 2:
            return
        step = graph_w / max_len
        points = [(graph_x + i * step, graph_y + graph_h - h * graph_h) for i, h in enumerate(history)]
        pygame.draw.lines(screen, color, False, points, 2)

    draw_curve(transmission_history_bottom, RED)
    draw_curve(transmission_history_top, BLUE)
    draw_curve(transmission_history_top2, (0, 255, 0))

    # Mise à jour des labels
    transmission_label_bottom.set_text(f"Transmission bas: {transmission_bottom*100:.1f}%")
    transmission_label_top.set_text(f"Transmission haut 1: {transmission_top*100:.1f}%")
    transmission_label_top2.set_text(f"Transmission haut 2: {transmission_top2*100:.1f}%")

def reset_simulation():
    global pulses, transmission_history_bottom, transmission_history_top, transmission_history_top2
    pulses = []
    transmission_history_bottom.clear()
    transmission_history_top.clear()
    transmission_history_top2.clear()

running = True
while running:
    time_delta = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == nl_slider:
                    non_linear_strength = nl_slider.get_current_value()
                elif event.ui_element == shg_slider:
                    shg_threshold = shg_slider.get_current_value()
                elif event.ui_element == crystal_slider:
                    crystal_height = crystal_slider.get_current_value()
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == reset_button:
                    reset_simulation()
        manager.process_events(event)

    manager.update(time_delta)

    emit_pulses()

    screen.fill(BLACK)

    # Draw optical elements
    draw_lens()
    draw_crystal()
    draw_beamsplitters()
    draw_diaphragm()
    draw_photodiodes()

    # Update and draw pulses
    for p in pulses[:]:
        p.update()
        p.draw(screen)
        if p.is_off_screen():
            pulses.remove(p)

    draw_transmission_graph()

    manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()
