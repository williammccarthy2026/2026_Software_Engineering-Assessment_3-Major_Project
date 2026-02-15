import pygame
import sys

# SCREEN DIMENSIONS
WIDTH, HEIGHT = 800, 600

# COLOURS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mars Lander Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)

# BUTTONS
class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

# MENU BUTTONS
start_button = Button("Start", WIDTH//2 - 100, 200, 200, 60)
level_select_button = Button("Level Select", WIDTH//2 - 100, 300, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, 400, 200, 60)

# LEVEL 1

def level_1():
    # --- SETTINGS ---
    GRAVITY = 0.1
    THRUST = 0.25
    START_FUEL = 500
    SAFE_SPEED = 3
    SKY = (255, 150, 100)
    GROUND = (200, 80, 30)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)

    # LANDER CLASS
    class Lander:
        def __init__(self):
            self.x = WIDTH // 2
            self.y = 100
            self.speed = 0
            self.fuel = START_FUEL
            self.alive = True
            self.width = 60
            self.height = 80
            self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)

        def update(self):
            if not self.alive:
                return
            self.speed += GRAVITY
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and self.fuel > 0:
                self.speed -= THRUST
                self.fuel -= 1
            self.y += self.speed
            self.rect.centery = self.y
            if self.y > HEIGHT - 100:
                self.y = HEIGHT - 100
                self.rect.centery = self.y
                self.alive = False

        def draw(self):
            pygame.draw.rect(screen, (255, 255, 0), self.rect)  # yellow rectangle for spaceship

    # GROUND CLASS
    class Ground:
        def draw(self):
            pygame.draw.rect(screen, GROUND, (0, HEIGHT-80, WIDTH, 80))
            pygame.draw.rect(screen, (150,150,150), (WIDTH//2-100, HEIGHT-90, 200, 20))

    # HUD CLASS
    class HUD:
        def draw(self, lander):
            altitude = HEIGHT - 100 - lander.y
            texts = [
                f"Altitude: {int(altitude)}",
                f"Speed: {lander.speed:.1f}",
                f"Fuel: {int(lander.fuel)}"
            ]
            for i, text in enumerate(texts):
                msg = font.render(text, True, WHITE)
                screen.blit(msg, (20, 20 + i*50))
            if not lander.alive:
                if lander.speed < SAFE_SPEED:
                    msg = font.render("SAFE LANDING!", True, GREEN)
                else:
                    msg = font.render("CRASHED!", True, RED)
                screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
                quit_msg = font.render("Press Q to quit", True, WHITE)
                screen.blit(quit_msg, (WIDTH//2 - 150, HEIGHT//2 + 20))

    # CREATING OBJECTS
    lander = Lander()
    ground = Ground()
    hud = HUD()

    # GAME LOOP
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q and not lander.alive:
                running = False  # return to menu

        lander.update()
        screen.fill(SKY)
        ground.draw()
        lander.draw()
        hud.draw(lander)

        pygame.display.flip()
        clock.tick(60)

# MAIN MENU

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
                    level_1()  # START LEVEL 1
                if level_select_button.is_hovered():
                    print("Level Select clicked")
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()

        for button in [start_button, level_select_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()

main_menu()