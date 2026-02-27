# TO DO
# - Add sound file





# ----------------------------------------
# Imported Libraries
# ----------------------------------------
import pygame # import the pygame library
import sys # import sys for exiting the program
import math # import math for rotation and speed calculations

# ----------------------------------------
# Game States
# ----------------------------------------
MENU = 'MENU'
PLAYING = 'PLAYING'
ENDED = 'ENDED'

# ----------------------------------------
# Constants
# ----------------------------------------
WIDTH = 1024 # screen width in pixels
HEIGHT = 750 # screen height in pixels
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
pygame.mixer.init() # initialize pygame mixer
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # create game window
pygame.display.set_caption("Mars Lander") # window title
clock = pygame.time.Clock() # control frame rate
font = pygame.font.Font(None, 50) # font for on-screen text

# Load background image
background_image = pygame.image.load("level1_mars-surface.png").convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# Load Sound Effects
thrust_sound = pygame.mixer.Sound("lander_thrust.wav") # Load thrust sound effect

# ----------------------------------------
# Menu Class
# ----------------------------------------
class Menu:
    def draw(self):
        screen.blit(background_image, (0, 0)) # Add background image
        title = font.render("Mars Lander", True, WHITE) # Draw title
        instructions = font.render("Press SPACE to start", True, WHITE) # instructions
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100)) # draw title
        screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 20)) # draw instructions

    def handle_event(self, event):
            if event.type == pygame.KEYDOWN: # Detects key press
                if event.key == pygame.K_SPACE: # Checks if space key pressed
                    return True # Starts the game
            return False

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
        self.boosterL_image = pygame.image.load("lander_(boosterL).png").convert_alpha() # Loads left booster image
        self.boosterR_image = pygame.image.load("lander_(boosterR).png").convert_alpha() # Loads right booster image

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

        # ----------
        # Controls
        # ----------
        if keys[pygame.K_SPACE] and self.fuel > 0: # Checks if space key is pressed and if fuel is left
            rad = math.radians(self.angle)
            self.speed_x -= math.sin(rad) * THRUST # Adjust horizontal speed based on angle
            self.speed_y -= math.cos(rad) * THRUST # Adjust vertical speed based on angle
            self.fuel -= 1 # Removes 1 fuel
            self.thrusting = True 
            thrust_sound.play() # Play thrust sound effect

        
        if keys[pygame.K_LEFT]: # Check for left arrow key press
            self.angle += 4 # Rotate the Lander
            self.image = self.boosterL_image
        if keys[pygame.K_RIGHT]:
            self.angle -= 4
            self.image = self.boosterR_image
    
        self.angle = max(-90, min(90, self.angle)) # limits the turning angle

        # ----------
        # Setting Lander Image
        # ----------
        if keys[pygame.K_LEFT]:
            image_to_rotate = self.boosterL_image
        elif keys[pygame.K_RIGHT]:
            image_to_rotate = self.boosterR_image
        elif self.thrusting:
            image_to_rotate = self.booster_image
        else:
            image_to_rotate = self.base_image

        # Rotate and update image
        self.image = pygame.transform.rotate(image_to_rotate, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

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
        altitude = HEIGHT - 100 - lander.y # distance above ground
        
        texts = [ # information to show
            f"Altitude: {int(altitude)}",
            f"Vertical Speed: {lander.speed_y:.1f}",
        ]
        
        for i, text in enumerate(texts): # display each line
            msg = font.render(text, True, WHITE)
            screen.blit(msg, (20, 20 + i*50))
            
        if not lander.alive: # show result when landed
            if abs(lander.speed_y) < SAFE_SPEED:
                msg = font.render("SAFE LANDING!", True, GREEN)
            else:
                msg = font.render("CRASHED!", True, RED)
            screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
            quit_msg = font.render("Press Q to quit", True, WHITE)
            screen.blit(quit_msg, (WIDTH//2 - 150, HEIGHT//2 + 20))


# ----------------------------------------
# Game Objects
# ----------------------------------------
lander = None # Lander
ground = Ground() # Mars ground
hud = HUD() # Information display
menu = Menu() # Start menu

# ----------------------------------------
# Game State   
# ----------------------------------------
game_state = MENU

# ----------------------------------------
# Main Game Loop
# ----------------------------------------
running = True
while running: # Main game loop

    # --------------------
    # Event Handling
    # --------------------
    for event in pygame.event.get(): # Check for events
        if event.type == pygame.QUIT: # Check for quit event
            running = False
        
        if game_state == MENU: # Check for menu events
            if menu.handle_event(event): # Start the game
                lander = Lander() # Create lander
                game_state = PLAYING # Switch to playing state
        # ----------
        # Ending Game
        # ----------
        elif game_state == ENDED: # Check for end game events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    lander = Lander() # Restart the game
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q: # Quit on Q key press
                running = False

        # ----------
        # Updating Game
        # ----------
        if game_state == PLAYING:
            lander.update() # Update lander position and state

            if lander.landed or not lander.alive: # Check for landing/crash
                game_state = ENDED # Switch to ended state

        # ----------
        # Drawing Everything
        # ----------
        screen.blit(background_image, (0, 0)) # Draw background image
        ground.draw() # Draw the ground
        if game_state == MENU:
            menu.draw() # Draw the menu
        else:
            lander.draw() # Draw the lander
            hud.draw(lander) # Draw the HUD

        # ----------
        # End Game Message
        # ----------
        if game_state == ENDED: # Show end game message
            if lander.landed:
                msg = font.render("SAFE LANDING!", True, GREEN) # Show safe landing message
                screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50)) # Center message
            else:
                msg = font.render("CRASHED!", True, RED) # Show crash message
            screen.blit(msg, (WIDTH//2 - 180, HEIGHT//2 - 50))
            quit_msg = font.render("Press Q to quit", True, WHITE) # Show quit message
            screen.blit(quit_msg, (WIDTH//2 - 150, HEIGHT//2 + 20))

    clock.tick(60) # Limit to 60 frames per second
    pygame.display.flip() # Update the display

pygame.quit() # Quit pygame
sys.exit() # Quit the game