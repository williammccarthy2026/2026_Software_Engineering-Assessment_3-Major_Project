import pygame
import sys
import random
from math import sin, cos, radians

# PYGAME INITIALISATION
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Fullscreen on any display
WIDTH, HEIGHT = screen.get_size()  # Get the actual screen resolution
pygame.display.set_caption("Mars Lander Game")
clock = pygame.time.Clock()

# COLOURS (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
SKY = (255, 150, 100)
GROUND = (200, 80, 30)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# GAME SETTINGS
GRAVITY = 0.04          # Much slower falling speed
THRUST = 0.20           # Thrust strength
ROTATION_SPEED = 1.5    # Slower turning (degrees per frame)
SAFE_VY = 3             # Max vertical speed for safe landing
SAFE_VX = 2             # Max horizontal speed for safe landing
SAFE_ANGLE = 10         # Max tilt angle for safe landing
GROUND_LEVEL = HEIGHT - 80  # Top of the ground (scales with screen height)
BOOSTER_INTERVAL = 30   # 0.5 seconds at 60 FPS

# BUTTON CLASS (for menu)
class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.SysFont(None, 50)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

# MENU BUTTONS (centered on any screen size)
start_button = Button("Start", WIDTH//2 - 100, HEIGHT//3, 200, 60)
level_select_button = Button("Level Select", WIDTH//2 - 100, HEIGHT//3 + 100, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, HEIGHT//3 + 200, 200, 60)

# LEVEL 1 FUNCTION
def level_1():
    # LANDER CLASS
    class Lander:
        def __init__(self):
            self.x = WIDTH // 2
            self.y = HEIGHT // 10  # Start higher up on larger screens
            self.vx = 0.0
            self.vy = 0.0
            self.angle = 0.0
            self.thrusting = False
            self.booster_timer = 0
            self.current_booster_index = 0
            self.alive = True
            self.landed_safely = False
            self.on_pad = False
            self.normal_image = pygame.image.load('lander.png').convert_alpha()
            self.booster_images = [pygame.image.load(f'lander_(boosterv{i}).png').convert_alpha() for i in range(1, 4)]
            self.half_width = self.normal_image.get_width() // 2
            self.half_height = self.normal_image.get_height() // 2

        def update(self, ground):
            if not self.alive:
                return

            self.vy += GRAVITY  # Gentle gravity

            keys = pygame.key.get_pressed()
            was_thrusting = self.thrusting
            self.thrusting = keys[pygame.K_SPACE]
            if self.thrusting:
                # Apply thrust in the direction the lander is facing
                self.vx += THRUST * sin(radians(self.angle))
                self.vy -= THRUST * cos(radians(self.angle))

                # Booster animation logic
                if not was_thrusting or self.booster_timer <= 0:
                    self.current_booster_index = random.randint(0, 2)
                    self.booster_timer = BOOSTER_INTERVAL
                self.booster_timer -= 1

            if keys[pygame.K_LEFT]:
                self.angle -= ROTATION_SPEED
            if keys[pygame.K_RIGHT]:
                self.angle += ROTATION_SPEED

            self.x += self.vx
            self.y += self.vy

            # Keep lander within screen bounds
            if self.x < self.half_width:
                self.x = self.half_width
                self.vx = 0
            if self.x > WIDTH - self.half_width:
                self.x = WIDTH - self.half_width
                self.vx = 0

            # Ground collision (using fixed half_height for consistency)
            if self.y + self.half_height >= GROUND_LEVEL:
                self.y = GROUND_LEVEL - self.half_height
                self.on_pad = ground.pad_x <= self.x <= ground.pad_x + ground.pad_width
                if self.on_pad and self.vy < SAFE_VY and abs(self.vx) < SAFE_VX and abs(self.angle) < SAFE_ANGLE:
                    self.landed_safely = True
                self.alive = False
                self.vx = 0
                self.vy = 0

        def draw(self):
            if self.thrusting:
                original = self.booster_images[self.current_booster_index]
            else:
                original = self.normal_image
            # Rotate and draw
            rotated = pygame.transform.rotate(original, -self.angle)
            rect = rotated.get_rect(center=(self.x, self.y))
            screen.blit(rotated, rect)

    # GROUND CLASS
    class Ground:
        def __init__(self):
            self.pad_width = 200
            self.pad_height = 20
            self.pad_x = random.randint(100, WIDTH - self.pad_width - 100)
            self.pad_y = HEIGHT - 90
            self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_width, self.pad_height)

        def draw(self):
            pygame.draw.rect(screen, GROUND, (0, GROUND_LEVEL, WIDTH, 80))
            pygame.draw.rect(screen, (150, 150, 150), self.pad_rect)

    # Simple landing message (no HUD, scaled font)
    def show_message(text, color):
        font_size = int(HEIGHT / 7.5)
        font = pygame.font.SysFont(None, font_size)
        msg = font.render(text, True, color)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        small_size = int(HEIGHT / 15)
        font_small = pygame.font.SysFont(None, small_size)
        quit_msg = font_small.render("Press Q or ESC to quit", True, WHITE)
        screen.blit(quit_msg, (WIDTH//2 - quit_msg.get_width()//2, HEIGHT//2 + 50))

    # Create objects
    lander = Lander()
    ground = Ground()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and not lander.alive:
                    running = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        lander.update(ground)
        screen.fill(SKY)
        ground.draw()
        lander.draw()

        # Show result message when landed
        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING!", GREEN)
            else:
                show_message("CRASHED!", RED)

        pygame.display.flip()
        clock.tick(60)

# MAIN MENU FUNCTION
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
                    print("Level Select clicked")  # Placeholder
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Update button colors on hover
        for button in [start_button, level_select_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

# Start the game
main_menu()