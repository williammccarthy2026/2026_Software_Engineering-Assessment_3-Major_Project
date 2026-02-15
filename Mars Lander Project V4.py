import pygame
import sys
import random
from math import sin, cos, radians

# PYGAME INITIALISATION
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Mars Lander Game")
clock = pygame.time.Clock()

# COLOURS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
SKY = (255, 150, 100)
GROUND = (200, 80, 30)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# GAME SETTINGS
GRAVITY = 0.04
THRUST = 0.20
ROTATION_SPEED = 1.5
SAFE_VY = 3
SAFE_VX = 2
SAFE_ANGLE = 10
GROUND_LEVEL = HEIGHT - 80
BOOSTER_INTERVAL = 30
EXPLOSION_FRAME_TIME = 12  # Slower: ~0.2 seconds per frame

# BUTTON CLASS (unchanged)
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

# MENU BUTTONS (unchanged)
start_button = Button("Start", WIDTH//2 - 100, HEIGHT//3, 200, 60)
level_select_button = Button("Level Select", WIDTH//2 - 100, HEIGHT//3 + 100, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, HEIGHT//3 + 200, 200, 60)

# LEVEL 1
def level_1():
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

            # Load images
            self.normal = pygame.image.load('lander.png').convert_alpha()
            self.booster_v = [
                pygame.image.load('lander_(boosterv1).png').convert_alpha(),
                pygame.image.load('lander_(boosterv2).png').convert_alpha(),
                pygame.image.load('lander_(boosterv3).png').convert_alpha()
            ]
            self.booster_left = pygame.image.load('lander_(boosterL).png').convert_alpha()
            self.booster_right = pygame.image.load('lander_(boosterR).png').convert_alpha()

            self.explosion_frames = [
                pygame.image.load('Explosion1.png').convert_alpha(),
                pygame.image.load('Explosion2.png').convert_alpha(),
                pygame.image.load('Explosion3.png').convert_alpha(),
                pygame.image.load('Explosion4.png').convert_alpha()
            ]

            self.half_width = self.normal.get_width() // 2
            self.half_height = self.normal.get_height() // 2

            # Explosion state
            self.explosion_frame = 0
            self.explosion_timer = 0
            self.explosion_active = False
            self.explosion_finished = False  # New flag

        def update(self, ground):
            if not self.alive:
                if self.crashed and self.explosion_active:
                    self.explosion_timer += 1
                    if self.explosion_timer >= EXPLOSION_FRAME_TIME:
                        self.explosion_timer = 0
                        self.explosion_frame += 1
                        if self.explosion_frame >= len(self.explosion_frames):
                            self.explosion_active = False
                            self.explosion_finished = True  # Stay on last frame
                return

            self.vy += GRAVITY

            keys = pygame.key.get_pressed()
            was_thrusting = self.thrusting
            self.thrusting = keys[pygame.K_SPACE]

            turning_left = keys[pygame.K_LEFT]
            turning_right = keys[pygame.K_RIGHT]

            if turning_left:
                self.angle -= ROTATION_SPEED
            if turning_right:
                self.angle += ROTATION_SPEED

            if self.thrusting:
                self.vx += THRUST * sin(radians(self.angle))
                self.vy -= THRUST * cos(radians(self.angle))

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

            if self.y + self.half_height >= GROUND_LEVEL:
                self.y = GROUND_LEVEL - self.half_height
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
                # After animation finishes, keep showing the last frame
                frame_idx = min(self.explosion_frame, len(self.explosion_frames) - 1)
                return self.explosion_frames[frame_idx]
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

    def show_message(text, color):
        font_size = int(HEIGHT / 7.5)
        font = pygame.font.SysFont(None, font_size)
        msg = font.render(text, True, color)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
        small_size = int(HEIGHT / 15)
        font_small = pygame.font.SysFont(None, small_size)
        quit_msg = font_small.render("Press Q or ESC to quit", True, WHITE)
        screen.blit(quit_msg, (WIDTH//2 - quit_msg.get_width()//2, HEIGHT//2 + 50))

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
        lander.update(ground)
        screen.fill(SKY)
        ground.draw()
        lander.draw()

        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING!", GREEN)
            elif lander.crashed:
                show_message("CRASHED!", RED)
            else:
                show_message("LANDED!", WHITE)

        pygame.display.flip()
        clock.tick(60)

# MAIN MENU (unchanged)
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
                    print("Level Select clicked")
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        for button in [start_button, level_select_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

main_menu()