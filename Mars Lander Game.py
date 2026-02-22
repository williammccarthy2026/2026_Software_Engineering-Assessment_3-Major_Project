# ----------------------------------------
# Imported Libraries
# ----------------------------------------
import pygame # import the pygame library
import sys # import sys for exiting the program
import math # import math for rotation and speed calculations

# ----------------------------------------
# Constants
# ----------------------------------------
WIDTH = 800 # screen width in pixels
HEIGHT = 600 # screen height in pixels
GRAVITY = 0.1 # how fast the lander falls
THRUST = 0.25 # how strong the space key thrust is
START_FUEL = 500 # starting amount of fuel
SAFE_SPEED = 3 # maximum safe landing speed

# ----------------------------------------
# Colours
# ----------------------------------------
SKY = (255, 150, 100)
GROUND = (200, 80, 30)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# ----------------------------------------
# Pygame Setup
# ----------------------------------------
pygame.init() # start pygame
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # create game window
pygame.display.set_caption("Mars Lander") # window title
clock = pygame.time.Clock() # control frame rate
font = pygame.font.Font(None, 50) # font for on-screen text


# ----------------------------------------
# Lander Class
# ----------------------------------------
class Lander:
    def __init__(self):
        # --------------------
        # Adding variables
        # --------------------
        self.x = WIDTH // 2 # Start in middle of screen
        self.y = 120 # Start near the top
        self.angle = 0 # start upright
        self.speed_y = 0 # vertical speed
        self.speed_x = 0 # horizontal speed
        
        self.alive = True
        self.landed = False
        self.fuel = START_FUEL#current fuel

        # --------------------
        # Loading and setting up images
        # --------------------
        self.base_image = pygame.image.load("lander.png").convert_alpha() # Loads lander image
        self.booster_image = pygame.image.load("lander_(boosterv1).png").convert_alpha() # Loads booster image

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Centers lander image on rectangle for positioning

    # --------------------
    # Tracking lander position
    # --------------------
    def update(self):
        if not self.alive: # tracks landers state
            return

        self.thrusting = False

        self.speed_y += GRAVITY # Gravity propels lander down

        keys = pygame.key.get_pressed() # Checks which keys are currently pressed

        if keys[pygame.K_SPACE] and self.fuel > 0: # Checks if space key is pressed and if fuel is left
            rad = math.radians(self.angle)
            self.speed_x -= math.sin(rad) * THRUST # Adjust horizontal speed based on angle
            self.speed_y -= math.cos(rad) * THRUST # Adjust vertical speed based on angle
            self.fuel -= 1 # Removes 1 fuel
            self.thrusting = True 

        
        if keys[pygame.K_LEFT]: # Check for left arrow key press
            self.angle += 4 # Rotate the Lander
        if keys[pygame.K_RIGHT]:
            self.angle -= 4
    
        self.angle = max(-90, min(90, self.angle)) # limits the turning angle

        # Rotate the correct base image depending on thrust
        if self.thrusting:
            rotated = pygame.transform.rotate(self.booster_image, self.angle)
        else:
            rotated = pygame.transform.rotate(self.base_image, self.angle)

        # Update image + keep centered
        self.image = rotated
        self.rect = self.image.get_rect(center=(self.x, self.y))   # center stays at (x,y)

        self.y += self.speed_y
        self.x += self.speed_x

        # --------------------
        # Landing and crash detection
        # --------------------
        if self.y > HEIGHT - 100:
            self.y = HEIGHT - 100
            self.rect.center = (self.x, self.y)
            if abs(self.speed_y) <= SAFE_SPEED and abs(self.angle) <= 12:
                self.landed = True
            else:
                self.alive = False

    def draw(self):
        screen.blit(self.image, self.rect)#draw the spaceship image


# ----------------------------------------
# Ground class
# ----------------------------------------
class Ground:
    def draw(self):
        pygame.draw.rect(screen, GROUND, (0, HEIGHT-50, WIDTH, 50))#main ground
        pygame.draw.rect(screen, (150, 150, 150), (WIDTH//2-100, HEIGHT-55, 200, 10))#flat landing pad


# ----------------------------------------
# HUD Class
# ----------------------------------------
class HUD:
    def draw(self, lander):
        altitude = HEIGHT - 100 - lander.y#distance above ground
        
        texts = [#information to show
            f"Altitude: {int(altitude)}",
            f"Vertical Speed: {lander.speed_y:.1f}",
        ]
        
        for i, text in enumerate(texts):#display each line
            msg = font.render(text, True, WHITE)
            screen.blit(msg, (20, 20 + i*50))
            
        if not lander.alive:#show result when landed
            if abs(lander.speed_y) < SAFE_SPEED:
                msg = font.render("SAFE LANDING!", True, GREEN)
            else:
                msg = font.render("CRASHED!", True, RED)
            screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
            quit_msg = font.render("Press Q to quit", True, WHITE)
            screen.blit(quit_msg, (WIDTH//2 - 150, HEIGHT//2 + 20))


# create the game objects
lander = Lander()#the spaceship
ground = Ground()#the mars ground
hud = HUD()#the information display

# ----------------------------------------
# Main Game Loop
# ----------------------------------------
while True:
    for event in pygame.event.get():#check for quit or key press
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q and not lander.alive:
            pygame.quit()
            sys.exit()

    
    lander.update()#move the lander
    
    screen.fill(SKY)#clear screen with sky
    ground.draw()#draw ground
    lander.draw()#draw spaceship
    hud.draw(lander)#draw text and results
    
    pygame.display.flip()#update the screen
    clock.tick(60)#run at 60 frames per second