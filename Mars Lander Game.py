import pygame
import sys
import random
from math import sin, cos, radians

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Mars Lander Game")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (200, 200, 200)
BLUE  = (50, 150, 255)
SKY   = (255, 150, 100)
GROUND = (200, 80, 30)
GREEN = (0, 255, 0)
RED   = (255, 0, 0)
LOCKED_GRAY = (100, 100, 100)

GRAVITY          = 0.04
THRUST           = 0.20
ROTATION_SPEED   = 1.0
SAFE_VY          = 3
SAFE_VX          = 2
SAFE_ANGLE       = 10
GROUND_LEVEL_FLAT = HEIGHT - 80
BOOSTER_INTERVAL = 30
EXPLOSION_FRAME_TIME = 12

class Button:
    def __init__(self, text, x, y, width, height, color=GRAY):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.SysFont(None, 50)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

# Menu buttons
start_button = Button("Start", WIDTH//2 - 150, HEIGHT//3, 300, 60)
level_select_button = Button("Level Select", WIDTH//2 - 150, HEIGHT//3 + 80, 300, 60)
exit_button = Button("Exit", WIDTH//2 - 150, HEIGHT//3 + 160, 300, 60)

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

    def update(self, ground, terrain_points=None, keys=None):
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

        if terrain_points:
            for i in range(len(terrain_points)-1):
                x1, y1 = terrain_points[i]
                x2, y2 = terrain_points[i+1]
                if x1 <= self.x <= x2:
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
        else:
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

    def get_current_image(self, keys):
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

    def draw(self, keys):
        img = self.get_current_image(keys)
        rotated = pygame.transform.rotate(img, -self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect)

def show_message(text, color):
    font_size = int(HEIGHT / 7.5)
    font = pygame.font.SysFont(None, font_size)
    msg = font.render(text, True, color)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))

    small_size = int(HEIGHT / 15)
    font_small = pygame.font.SysFont(None, small_size)
    quit_msg = font_small.render("Press Q or ESC to quit", True, WHITE)
    screen.blit(quit_msg, (WIDTH//2 - quit_msg.get_width()//2, HEIGHT//2 + 50))

# Level 1 - Flat ground
def level_1(level2_unlocked):
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
    won = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                if won and event.key == pygame.K_SPACE:
                    running = False  # Proceed to Level 2 after SPACE

        keys = pygame.key.get_pressed()
        lander.update(ground, keys=keys)
        screen.fill(SKY)
        ground.draw()
        lander.draw(keys)

        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING! Press SPACE to go to Level 2", GREEN)
                level2_unlocked[0] = True
                won = True
            elif lander.crashed:
                show_message("CRASHED!", RED)
                pygame.display.flip()
                pygame.time.wait(3000)
                running = False

        pygame.display.flip()
        clock.tick(60)

    return level2_unlocked

# Level 2 - Uneven terrain
def level_2():
    class UnevenGround:
        def __init__(self):
            self.pad_width  = 120
            self.pad_height = 20
            self.terrain_points = []
            x = 0
            y = GROUND_LEVEL_FLAT + random.randint(-40, 40)
            while x < WIDTH:
                self.terrain_points.append((x, y))
                x += random.randint(80, 150)
                y += random.randint(-60, 60)
                y = max(HEIGHT // 2, min(HEIGHT - 100, y))
            self.terrain_points.append((WIDTH, self.terrain_points[-1][1]))

            flat_spot = random.randint(3, len(self.terrain_points)-5)
            pad_center_x = (self.terrain_points[flat_spot][0] + self.terrain_points[flat_spot+1][0]) // 2
            self.pad_x = pad_center_x - self.pad_width // 2
            self.pad_y = min(self.terrain_points[flat_spot][1], self.terrain_points[flat_spot+1][1]) - self.pad_height
            self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_width, self.pad_height)

        def draw(self):
            pygame.draw.polygon(screen, GROUND, self.terrain_points + [(WIDTH, HEIGHT), (0, HEIGHT)])
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
                    running = False

        keys = pygame.key.get_pressed()
        lander.update(ground, terrain_points=ground.terrain_points, keys=keys)
        screen.fill(SKY)
        ground.draw()
        lander.draw(keys)

        if not lander.alive:
            if lander.landed_safely:
                show_message("SAFE LANDING! Level 2 Complete", GREEN)
            elif lander.crashed:
                show_message("CRASHED!", RED)
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False

        pygame.display.flip()
        clock.tick(60)

# Level Select screen
def level_select(level2_unlocked):
    level1_btn = Button("Level 1", WIDTH//2 - 150, HEIGHT//3, 300, 60)
    level2_btn = Button("Level 2", WIDTH//2 - 150, HEIGHT//3 + 80, 300, 60, color=BLUE if level2_unlocked[0] else LOCKED_GRAY)
    back_btn = Button("Back", WIDTH//2 - 150, HEIGHT//3 + 160, 300, 60)

    running = True
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if level1_btn.is_hovered():
                    level_1(level2_unlocked)
                if level2_btn.is_hovered() and level2_unlocked[0]:
                    level_2()
                if back_btn.is_hovered():
                    running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        level1_btn.draw(screen)
        level2_btn.draw(screen)
        back_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)

# Main menu
def main_menu():
    level2_unlocked = [False]

    running = True
    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_hovered():
                    level2_unlocked = level_1(level2_unlocked)
                    # After Level 1 finishes, check if won → prompt for Level 2
                    if level2_unlocked[0]:
                        screen.fill(WHITE)
                        show_message("Level 1 Complete! Press SPACE for Level 2", GREEN)
                        pygame.display.flip()
                        waiting = True
                        while waiting:
                            for ev in pygame.event.get():
                                if ev.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                                if ev.type == pygame.KEYDOWN:
                                    if ev.key == pygame.K_SPACE:
                                        level_2()
                                        waiting = False
                                    elif ev.key in (pygame.K_q, pygame.K_ESCAPE):
                                        waiting = False
                if level_select_button.is_hovered():
                    level_select(level2_unlocked)
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