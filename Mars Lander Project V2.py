import pygame
import sys

# SCREEN DIMENSIONS
WIDTH, HEIGHT = 800, 600  # Screen width and height in pixels

# COLOURS (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)

# PYGAME INITIALISATION
pygame.init()  # Initialize all pygame modules
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Create the game window
pygame.display.set_caption("Mars Lander Game")  # Window title
clock = pygame.time.Clock()  # Clock to control FPS
font = pygame.font.SysFont(None, 50)  # Default font and size

# BUTTON CLASS
class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text  # Text displayed on the button
        self.rect = pygame.Rect(x, y, width, height)  # Button rectangle
        self.color = GRAY  # Default button color

    def draw(self, screen):
        # Draw the button rectangle
        pygame.draw.rect(screen, self.color, self.rect)
        # Draw the text centered on the button
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self):
        # Returns True if the mouse is over the button
        return self.rect.collidepoint(pygame.mouse.get_pos())

# MENU BUTTONS
start_button = Button("Start", WIDTH//2 - 100, 200, 200, 60)
level_select_button = Button("Level Select", WIDTH//2 - 100, 300, 200, 60)
exit_button = Button("Exit", WIDTH//2 - 100, 400, 200, 60)

# LEVEL 1 FUNCTION
def level_1():
    # GAME SETTINGS
    GRAVITY = 0.1  # How fast the lander falls
    THRUST = 0.25  # How much upward force the lander generates
    START_FUEL = 500  # Initial fuel
    SAFE_SPEED = 3  # Maximum speed for a safe landing
    SKY = (255, 150, 100)  # Sky background color
    GROUND = (200, 80, 30)  # Ground color
    GREEN = (0, 255, 0)  # Color for safe landing message
    RED = (255, 0, 0)  # Color for crash message

    # LANDER CLASS
    class Lander:
        def __init__(self):
            self.x = WIDTH // 2  # Starting x position
            self.y = 100  # Starting y position
            self.speed = 0  # Vertical speed
            self.fuel = START_FUEL
            self.alive = True  # Alive status
            self.width = 60
            self.height = 80
            self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)

        def update(self):
            if not self.alive:
                return  # Do nothing if landed/crashed

            self.speed += GRAVITY  # Apply gravity

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and self.fuel > 0:
                self.speed -= THRUST  # Apply upward thrust
                self.fuel -= 1  # Reduce fuel

            self.y += self.speed  # Move lander vertically
            self.rect.centery = self.y  # Update rectangle position

            # Check for collision with ground
            if self.y > HEIGHT - 100:
                self.y = HEIGHT - 100
                self.rect.centery = self.y
                self.alive = False  # Landed/crashed

        def draw(self):
            # Draw lander as yellow rectangle
            pygame.draw.rect(screen, (255, 255, 0), self.rect)

    # GROUND CLASS
    class Ground:
        def draw(self):
            # Draw main ground
            pygame.draw.rect(screen, GROUND, (0, HEIGHT-80, WIDTH, 80))
            # Draw landing pad
            pygame.draw.rect(screen, (150,150,150), (WIDTH//2-100, HEIGHT-90, 200, 20))

    # HUD CLASS
    class HUD:
        def draw(self, lander):
            altitude = HEIGHT - 100 - lander.y  # Calculate altitude
            texts = [
                f"Altitude: {int(altitude)}",
                f"Speed: {lander.speed:.1f}",
                f"Fuel: {int(lander.fuel)}"
            ]
            # Display altitude, speed, and fuel
            for i, text in enumerate(texts):
                msg = font.render(text, True, WHITE)
                screen.blit(msg, (20, 20 + i*50))

            # Display landing/crash messages if lander is not alive
            if not lander.alive:
                if lander.speed < SAFE_SPEED:
                    msg = font.render("SAFE LANDING!", True, GREEN)
                else:
                    msg = font.render("CRASHED!", True, RED)
                screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
                quit_msg = font.render("Press Q to quit", True, WHITE)
                screen.blit(quit_msg, (WIDTH//2 - 150, HEIGHT//2 + 20))


    # CREATE OBJECTS
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
                running = False  # Return to menu

        lander.update()  # Update lander position and state
        screen.fill(SKY)  # Clear screen with sky color
        ground.draw()  # Draw ground
        lander.draw()  # Draw lander
        hud.draw(lander)  # Draw HUD

        pygame.display.flip()  # Update display
        clock.tick(60)  # Limit to 60 FPS


# MAIN MENU FUNCTION
def main_menu():
    running = True
    while running:
        screen.fill(WHITE)  # Clear screen

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check which button was clicked
                if start_button.is_hovered():
                    level_1()  # Start Level 1
                if level_select_button.is_hovered():
                    print("Level Select clicked")  # Placeholder
                if exit_button.is_hovered():
                    pygame.quit()
                    sys.exit()

        # Draw buttons and highlight on hover
        for button in [start_button, level_select_button, exit_button]:
            button.color = BLUE if button.is_hovered() else GRAY
            button.draw(screen)

        pygame.display.flip()  # Update display

main_menu()
