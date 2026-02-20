import pygame               # Main library for game development
import sys                  # For system-level operations (like exiting the program)
import random               # For random numbers (landing pad position, booster animation)
from math import sin, cos, radians  # Math functions for thrust direction calculation

# ────────────────────────────────────────────────
#  PYGAME INITIALISATION
# ────────────────────────────────────────────────
pygame.init()                           # Start all pygame modules
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Open fullscreen window
WIDTH, HEIGHT = screen.get_size()       # Get actual screen resolution
pygame.display.set_caption("Mars Lander Game")  # Set window title
clock = pygame.time.Clock()             # Clock to control frame rate

# ────────────────────────────────────────────────
#  COLOUR DEFINITIONS (RGB tuples)
# ────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (200, 200, 200)
BLUE  = (50, 150, 255)
SKY   = (255, 150, 100)     # Orange-ish martian sky
GROUND = (200, 80, 30)      # Martian ground colour
GREEN = (0, 255, 0)         # Success message colour
RED   = (255, 0, 0)         # Crash message colour

# ────────────────────────────────────────────────
#  GAME CONSTANTS / TUNING VALUES
# ────────────────────────────────────────────────
GRAVITY          = 0.04             # Acceleration downward each frame (low = floaty feel)
THRUST           = 0.20             # Thrust power when engine is on
ROTATION_SPEED   = 1.0              # Slightly faster turning (was 0.8)
SAFE_VY          = 3                # Max safe vertical landing speed
SAFE_VX          = 2                # Max safe horizontal landing speed
SAFE_ANGLE       = 10               # Max acceptable tilt angle at landing (degrees)
GROUND_LEVEL_FLAT = HEIGHT - 80     # Flat ground level for level 1
BOOSTER_INTERVAL = 30               # Frames between booster flame changes (~0.5s @ 60fps)
EXPLOSION_FRAME_TIME = 12           # Frames each explosion image is shown (~0.2s per frame)

# ────────────────────────────────────────────────
#  SIMPLE BUTTON CLASS FOR MAIN MENU
# ────────────────────────────────────────────────
class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY               # Default colour when not hovered

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.SysFont(None, 50)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

# Create menu buttons (positions relative to screen center)
start_button = Button("Start Level 1", WIDTH//2 - 100, HEIGHT//3, 200, 60)
level2_button = Button("Start Level 2", WIDTH//2 - 100, HEIGHT//3 + 80, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, HEIGHT//3 + 160, 200, 60)

# ────────────────────────────────────────────────
#  SHARED LANDER CLASS (used by both levels)
# ────────────────────────────────────────────────
class Lander:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 10
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.thrusting = False
        self.booster_timer = 0
        self.current_booster_index = 0
        self.alive = True
        self.landed_safely = False
        self.crashed = False
        self.on_pad = False

        self.normal = pygame.image.load('lander.png').convert_alpha()
        self.booster_v = [
            pygame.image.load('lander_(boosterv1).png').convert_alpha(),
            pygame.image.load('lander_(boosterv2).png').convert_alpha(),
            pygame.image.load('lander_(boosterv3).png').convert_alpha()
        ]
        self.booster_left  = pygame.image.load('lander_(boosterL).png').convert_alpha()
        self.booster_right = pygame.image.load('lander_(boosterR).png').convert_alpha()

        self.explosion_frames = [
            pygame.image.load('Explosion1.png').convert_alpha(),
            pygame.image.load('Explosion2.png').convert_alpha(),
            pygame.image.load('Explosion3.png').convert_alpha(),
            pygame.image.load('Explosion4.png').convert_alpha()
        ]

        self.half_width  = self.normal.get_width()  // 2
        self.half_height = self.normal.get_height() // 2

        self.explosion_frame   = 0
        self.explosion_timer   = 0
        self.explosion_active  = False
        self.explosion_finished = False

    def update(self, ground, terrain_points=None):
        if not self.alive:
            if self.crashed and self.explosion_active:
                self.explosion_timer += 1
                if self.explosion_timer >= EXPLOSION_FRAME_TIME:
                    self.explosion_timer = 0
                    self.explosion_frame += 1
                    if self.explosion_frame >= len(self.explosion_frames):
                        self.explosion_active = False
                        self.explosion_finished = True
            return

        self.vy += GRAVITY

        keys = pygame.key.get_pressed()
        was_thrusting = self.thrusting
        self.thrusting = keys[pygame.K_SPACE]

        turning_left  = keys[pygame.K_LEFT]
        turning_right = keys[pygame.K_RIGHT]

        if turning_left:
            self.angle -= ROTATION_SPEED
        if turning_right:
            self.angle += ROTATION_SPEED

        if self.thrusting:
            rad = radians(self.angle)
            self.vx += THRUST * sin(rad)
            self.vy -= THRUST * cos(rad)

            if not was_thrusting or self.booster_timer <= 0:
                self.current_booster_index = random.randint(0, 2)
                self.booster_timer = BOOSTER_INTERVAL
            self.booster_timer -= 1

        self.x += self.vx
        self.y += self.vy

        if self.x < self.half_width:
            self.x = self.half_width
            self.vx = 0
        if self.x > WIDTH - self.half_width:
            self.x = WIDTH - self.half_width
            self.vx = 0

        # ─── Collision with ground / terrain ───
        if terrain_points:  # Level 2: uneven terrain
            # Simple point-in-polygon check isn't perfect, but we approximate
            # by finding the ground y at current x and checking if lander bottom is below it
            for i in range(len(terrain_points)-1):
                x1, y1 = terrain_points[i]
                x2, y2 = terrain_points[i+1]
                if x1 <= self.x <= x2:
                    # Linear interpolation for ground height at x
                    ground_y = y1 + (y2 - y1) * (self.x - x1) / (x2 - x1)
                    if self.y + self.half_height >= ground_y:
                        self.y = ground_y - self.half_height
                        self.on_pad = ground.pad_x <= self.x <= ground.pad_x + ground.pad_width
                        if self.on_pad and self.vy < SAFE_VY and abs(self.vx) < SAFE_VX and abs(self.angle) < SAFE_ANGLE:
                            self.landed_safely = True
                        else:
                            self.crashed = True
                            self.explosion_active = True
                            self.explosion_frame = 0
                            self.explosion_timer = 0
                            self.explosion_finished = False
                        self.alive = False
                        self.vx = 0
                        self.vy = 0
                        return
        else:  # Level 1: flat ground
            if self.y + self.half_height >= GROUND_LEVEL_FLAT:
                self.y = GROUND_LEVEL_FLAT - self.half_height
                self.on_pad = ground.pad_x <= self.x <= ground.pad_x + ground.pad_width
                if self.on_pad and self.vy < SAFE_VY and abs(self.vx) < SAFE_VX and abs(self.angle) < SAFE_ANGLE:
                    self.landed_safely = True
                else:
                    self.crashed = True
                    self.explosion_active = True
                    self.explosion_frame = 0
                    self.explosion_timer = 0
                    self.explosion_finished = False
                self.alive = False
                self.vx = 0
                self.vy = 0

    def get_current_image(self):
        if self.explosion_active or self.explosion_finished:
            idx = min(self.explosion_frame, len(self.explosion_frames) - 1)
            return self.explosion_frames[idx]

        if self.thrusting:
            return self.booster_v[self.current_booster_index]
        elif keys[pygame.K_LEFT]:
            return self.booster_left
        elif keys[pygame.K_RIGHT]:
            return self.booster_right
        else:
            return self.normal

    def draw(self):
        img = self.get_current_image()
        rotated = pygame.transform.rotate(img, -self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect)

# ────────────────────────────────────────────────
#  LEVEL 1 – Flat ground
# ────────────────────────────────────────────────
def level_1():
    class Ground:
        def __init__(self):
            self.pad_width  = 120
            self.pad_height = 20
            self.pad_x = random.randint(100, WIDTH - self.pad_width - 100)
            self.pad_y = GROUND_LEVEL_FLAT - 10
            self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_width, self.pad_height)

        def draw(self):
            pygame.draw.rect(screen, GROUND, (0, GROUND_LEVEL_FLAT, WIDTH, HEIGHT - GROUND_LEVEL_FLAT))
            pygame.draw.rect(screen, (150, 150, 150), self.pad_rect)

    lander = Lander()
    ground = Ground()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    if not lander.alive:
                        running = False
                    else:
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()
        lander.update(ground)  # flat ground → no terrain_points
        screen.fill(SKY)
        ground.draw()
        lander.draw()

        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING! Level 1 Complete", GREEN)
            elif lander.crashed:
                show_message("CRASHED!", RED)
            else:
                show_message("LANDED!", WHITE)

        pygame.display.flip()
        clock.tick(60)

# ────────────────────────────────────────────────
#  LEVEL 2 – Uneven terrain
# ────────────────────────────────────────────────
def level_2():
    class UnevenGround:
        def __init__(self):
            self.pad_width  = 120
            self.pad_height = 20
            # Generate jagged terrain points
            self.terrain_points = []
            x = 0
            y = GROUND_LEVEL_FLAT + random.randint(-40, 40)
            while x < WIDTH:
                self.terrain_points.append((x, y))
                x += random.randint(80, 150)
                y += random.randint(-60, 60)  # height variation
                y = max(HEIGHT // 2, min(HEIGHT - 100, y))  # keep reasonable
            self.terrain_points.append((WIDTH, self.terrain_points[-1][1]))

            # Place pad on a relatively flat-ish section
            flat_spot = random.randint(3, len(self.terrain_points)-5)
            pad_center_x = (self.terrain_points[flat_spot][0] + self.terrain_points[flat_spot+1][0]) // 2
            self.pad_x = pad_center_x - self.pad_width // 2
            self.pad_y = min(self.terrain_points[flat_spot][1], self.terrain_points[flat_spot+1][1]) - self.pad_height
            self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_width, self.pad_height)

        def draw(self):
            # Draw jagged ground polygon
            pygame.draw.polygon(screen, GROUND, self.terrain_points + [(WIDTH, HEIGHT), (0, HEIGHT)])
            # Draw landing pad on top
            pygame.draw.rect(screen, (150, 150, 150), self.pad_rect)

    lander = Lander()
    ground = UnevenGround()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    if not lander.alive:
                        running = False
                    else:
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()
        lander.update(ground, terrain_points=ground.terrain_points)  # pass terrain for collision
        screen.fill(SKY)
        ground.draw()
        lander.draw()

        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING! Level 2 Complete", GREEN)
            elif lander.crashed:
                show_message("CRASHED!", RED)
            else:
                show_message("LANDED!", WHITE)

        pygame.display.flip()
        clock.tick(60)

# ────────────────────────────────────────────────
#  SHARED MESSAGE FUNCTION
# ────────────────────────────────────────────────
def show_message(text, color):
    font_size = int(HEIGHT / 7.5)
    font = pygame.font.SysFont(None, font_size)
    msg = font.render(text, True, color)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))

    small_size = int(HEIGHT / 15)
    font_small = pygame.font.SysFont(None, small_size)
    quit_msg = font_small.render("Press Q or ESC to quit", True, WHITE)
    screen.blit(quit_msg, (WIDTH//2 - quit_msg.get_width()//2, HEIGHT//2 + 50))

# ────────────────────────────────────────────────
#  MAIN MENU LOOP
# ────────────────────────────────────────────────
def main_menu():
    running = True
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_hovered():
                    level_1()
                if level2_button.is_hovered():
                    level_2()
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        for button in [start_button, level2_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

# ─── Start the game ───
main_menu()