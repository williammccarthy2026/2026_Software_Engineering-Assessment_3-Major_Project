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
#piuahwpiudhsapiuhds
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
ROTATION_SPEED   = 1.5              # Degrees per frame when turning
SAFE_VY          = 3                # Max safe vertical landing speed
SAFE_VX          = 2                # Max safe horizontal landing speed
SAFE_ANGLE       = 10               # Max acceptable tilt angle at landing (degrees)
GROUND_LEVEL     = HEIGHT - 80      # Y-coordinate of the top of the ground
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
        # Draw rectangle background
        pygame.draw.rect(screen, self.color, self.rect)
        # Render and center text
        font = pygame.font.SysFont(None, 50)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        # Check if mouse is currently over this button
        return self.rect.collidepoint(pygame.mouse.get_pos())

# Create menu buttons (positions are relative to screen center)
start_button = Button("Start", WIDTH//2 - 100, HEIGHT//3, 200, 60)
level_select_button = Button("Level Select", WIDTH//2 - 100, HEIGHT//3 + 100, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, HEIGHT//3 + 200, 200, 60)

# ────────────────────────────────────────────────
#  MAIN GAME LEVEL FUNCTION
# ────────────────────────────────────────────────
def level_1():
    # ──────────────────────────────
    #  Lander class – contains all ship logic
    # ──────────────────────────────
    class Lander:
        def __init__(self):
            # Starting position (center top-ish)
            self.x = WIDTH // 2
            self.y = HEIGHT // 10
            self.vx = 0.0               # Horizontal velocity
            self.vy = 0.0               # Vertical velocity
            self.angle = 0.0            # Rotation in degrees (0 = upright)
            self.thrusting = False
            self.booster_timer = 0
            self.current_booster_index = 0
            self.alive = True
            self.landed_safely = False
            self.crashed = False
            self.on_pad = False

            # ─── Load all possible images ───
            self.normal = pygame.image.load('lander.png').convert_alpha()
            self.booster_v = [
                pygame.image.load('lander_(boosterv1).png').convert_alpha(),
                pygame.image.load('lander_(boosterv2).png').convert_alpha(),
                pygame.image.load('lander_(boosterv3).png').convert_alpha()
            ]
            self.booster_left  = pygame.image.load('lander_(boosterL).png').convert_alpha()
            self.booster_right = pygame.image.load('lander_(boosterR).png').convert_alpha()

            # Explosion animation frames (played only on crash)
            self.explosion_frames = [
                pygame.image.load('Explosion1.png').convert_alpha(),
                pygame.image.load('Explosion2.png').convert_alpha(),
                pygame.image.load('Explosion3.png').convert_alpha(),
                pygame.image.load('Explosion4.png').convert_alpha()
            ]

            # Half-size values used for collision / boundary checks
            self.half_width  = self.normal.get_width()  // 2
            self.half_height = self.normal.get_height() // 2

            # Explosion animation control
            self.explosion_frame   = 0
            self.explosion_timer   = 0
            self.explosion_active  = False
            self.explosion_finished = False     # After animation → stay on last frame

        def update(self, ground):
            # If already landed or crashed → only update explosion if active
            if not self.alive:
                if self.crashed and self.explosion_active:
                    self.explosion_timer += 1
                    if self.explosion_timer >= EXPLOSION_FRAME_TIME:
                        self.explosion_timer = 0
                        self.explosion_frame += 1
                        if self.explosion_frame >= len(self.explosion_frames):
                            self.explosion_active = False
                            self.explosion_finished = True  # Lock on final frame
                return

            # Apply gravity every frame
            self.vy += GRAVITY

            # Read keyboard state
            keys = pygame.key.get_pressed()
            was_thrusting = self.thrusting
            self.thrusting = keys[pygame.K_SPACE]

            turning_left  = keys[pygame.K_LEFT]
            turning_right = keys[pygame.K_RIGHT]

            # Rotate ship
            if turning_left:
                self.angle -= ROTATION_SPEED
            if turning_right:
                self.angle += ROTATION_SPEED

            # Apply thrust in the direction the nose is pointing
            if self.thrusting:
                rad = radians(self.angle)
                self.vx += THRUST * sin(rad)        # horizontal component
                self.vy -= THRUST * cos(rad)        # vertical component (up is negative)

                # Cycle booster flame images randomly every ~0.5 seconds
                if not was_thrusting or self.booster_timer <= 0:
                    self.current_booster_index = random.randint(0, 2)
                    self.booster_timer = BOOSTER_INTERVAL
                self.booster_timer -= 1

            # Update position
            self.x += self.vx
            self.y += self.vy

            # Keep ship inside screen horizontally
            if self.x < self.half_width:
                self.x = self.half_width
                self.vx = 0
            if self.x > WIDTH - self.half_width:
                self.x = WIDTH - self.half_width
                self.vx = 0

            # Check landing / crash
            if self.y + self.half_height >= GROUND_LEVEL:
                self.y = GROUND_LEVEL - self.half_height
                # Check if centered on landing pad
                self.on_pad = ground.pad_x <= self.x <= ground.pad_x + ground.pad_width

                # Safe landing conditions
                if (self.on_pad and
                    self.vy < SAFE_VY and
                    abs(self.vx) < SAFE_VX and
                    abs(self.angle) < SAFE_ANGLE):
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
            # Priority: explosion > thrust > left turn > right turn > normal
            if self.explosion_active or self.explosion_finished:
                # After animation ends → keep showing last explosion frame
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
            # Get correct sprite, rotate it, and draw centered at (x,y)
            img = self.get_current_image()
            rotated = pygame.transform.rotate(img, -self.angle)
            rect = rotated.get_rect(center=(self.x, self.y))
            screen.blit(rotated, rect)

    # ──────────────────────────────
    #  Ground / landing pad
    # ──────────────────────────────
    class Ground:
        def __init__(self):
            self.pad_width  = 200
            self.pad_height = 20
            # Random horizontal position (with safe margins)
            self.pad_x = random.randint(100, WIDTH - self.pad_width - 100)
            self.pad_y = HEIGHT - 90
            self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_width, self.pad_height)

        def draw(self):
            # Draw ground rectangle
            pygame.draw.rect(screen, GROUND, (0, GROUND_LEVEL, WIDTH, 80))
            # Draw landing pad on top
            pygame.draw.rect(screen, (150, 150, 150), self.pad_rect)

    # ──────────────────────────────
    #  Show large centered message
    # ──────────────────────────────
    def show_message(text, color):
        font_size = int(HEIGHT / 7.5)           # Scale with screen height
        font = pygame.font.SysFont(None, font_size)
        msg = font.render(text, True, color)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))

        small_size = int(HEIGHT / 15)
        font_small = pygame.font.SysFont(None, small_size)
        quit_msg = font_small.render("Press Q or ESC to quit", True, WHITE)
        screen.blit(quit_msg, (WIDTH//2 - quit_msg.get_width()//2, HEIGHT//2 + 50))

    # ─── Create game objects ───
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
                        running = False             # Return to menu after landing/crash
                    else:
                        pygame.quit()
                        sys.exit()                  # Immediate exit during play

        keys = pygame.key.get_pressed()     # Used in draw() for side boosters
        lander.update(ground)
        screen.fill(SKY)
        ground.draw()
        lander.draw()

        # Show result text when game is over
        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING!", GREEN)
            elif lander.crashed:
                show_message("CRASHED!", RED)
            else:
                show_message("LANDED!", WHITE)

        pygame.display.flip()
        clock.tick(60)                      # Target 60 FPS

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
                if level_select_button.is_hovered():
                    print("Level Select clicked")   # Placeholder
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Highlight buttons when hovered
        for button in [start_button, level_select_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

# ─── Start the game ───
main_menu()
