# ----------------------------------------
# Imported Libraries
# ----------------------------------------
import pygame
import sys 
import math 
import os
import shutil
import datetime

# ----------------------------------------
# Backup Procedures
# ----------------------------------------
# Define the source and backup directories
SOURCE_FOLDER = "/Users/williammccarthy/Desktop/12SWEA/Assessment 3 - Major Project/Mars Lander" # The folder that contains files to be backed up
BACKUP_FOLDER = "/Users/williammccarthy/Desktop" # The destination folder where backups will be stored

# Generate a timestamp to create a unique backup folder
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Format: YYYY-MM-DD_HH-MM-SS
backup_path = os.path.join(BACKUP_FOLDER, f"Assessment 3 Backups{timestamp}") # Backup folder name includes timestamp

# Ensure the backup directory exists; create it if it doesn't
os.makedirs(backup_path, exist_ok=True) # `exist_ok=True` prevents errors if the folder already exists

shutil.copytree(SOURCE_FOLDER, backup_path, dirs_exist_ok=True) # Copy all files from source to backup

# Print a confirmation message after files are copied
print(f"Backup completed successfully! Files saved in: {backup_path}")

# ----------------------------------------
# Game States
# ----------------------------------------
MENU = 'MENU'
PLAYING = 'PLAYING'
ENDED = 'ENDED'
PAUSED = 'PAUSED'

# ----------------------------------------
# Constants
# ----------------------------------------
WIDTH = 1200 # screen width in pixels
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
BLACK = (0, 0, 0)
EMERALD = (21, 119, 40)
GREY = (107, 107, 107)
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
menu_screen = pygame.image.load("menu_screen.png").convert() # Load menu background image
menu_screen = pygame.transform.scale(menu_screen, (WIDTH, HEIGHT)) # Scale menu background to fit screen
background_image = pygame.image.load("level1_mars-surface.png").convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# Load Sound Effects
thrust_sound = pygame.mixer.Sound("lander_thrust.mp3") # Load thrust sound effect
thrust_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound("lander_explode.wav")
menu_button_hover = pygame.mixer.Sound("menu_button_hover.wav")
menu_button_accept = pygame.mixer.Sound("menu_button_accept.wav")
menu_button_accept.set_volume(0.1)

# ----------------------------------------
# Button Class
# ----------------------------------------
class Button:
    def __init__(self, x, y, width, height, text, action): # Initialize button with position, size, text, and action
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.font = pygame.font.Font(None, 40)
        self.hovered_last_frame = False # Track if button was hovered in the last frame to control sound playback

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos() 
        hovered = self.rect.collidepoint(mouse_pos) # Check if mouse is hovering over the button

        if hovered and not self.hovered_last_frame: # Play hover sound only when the button is first hovered over
            menu_button_hover.play()
        self.hovered_last_frame = hovered

        if hovered: # Change button appearance when hovered
            fill_colour = EMERALD
            outline_colour = BLACK
            text_colour = BLACK
        else: # Normal button appearance
            fill_colour = BLACK
            outline_colour = GREY
            text_colour = GREY

        pygame.draw.rect(screen, fill_colour, self.rect) # Draw button background
        pygame.draw.rect(screen, outline_colour, self.rect, 3) # Draw button outline

        label = self.font.render(self.text, True, text_colour) # Render the button text
        label_rect = label.get_rect(center=self.rect.center) # Center the text on the button
        screen.blit(label, label_rect) # Draw the text on the button

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return self.action # Return the action associated with the button when clicked

# ----------------------------------------
# Menu Class
# ----------------------------------------
class Menu:
    def __init__(self):
        self.button_width = 260
        self.button_height = 75
        self.spacing = 20
        self.margin_x = 50  # distance from left edge
        self.margin_y = 50  # distance from bottom edge

        # Compute starting Y so buttons stack upwards from bottom-left
        start_y = HEIGHT - self.margin_y - (self.button_height * 3 + self.spacing * 2)

        # Button rectangles
        self.buttons = [
        Button(self.margin_x, start_y, self.button_width, self.button_height, "Tutorial", "TUTORIAL"),
        Button(self.margin_x, start_y + self.button_height + self.spacing, self.button_width, self.button_height, "Begin", "BEGIN"),
        Button(self.margin_x, start_y + (self.button_height + self.spacing) * 2, self.button_width, self.button_height, "Exit", "EXIT")
    ]

    def draw_button(self, rect, text):
        mouse_pos = pygame.mouse.get_pos()

        if rect.collidepoint(mouse_pos): # Change button colour when hovered
            colour = (220, 220, 220)
        else:
            colour = (180, 180, 180) # Normal button colour

        pygame.draw.rect(screen, colour, rect, border_radius=10)

        label = self.button_font.render(text, True, (0,0,0))
        label_rect = label.get_rect(center=rect.center)
        screen.blit(label, label_rect)

    def draw(self):
        screen.blit(menu_screen, (0,0))

        # Draw buttons only (no title)
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event):
        for button in self.buttons:
            action = button.handle_event(event)
            if action:
                menu_button_accept.play() # Play accept sound when a button is clicked
                return action

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
        
        self.thrust_sound_playing = False # Track if thrust sound is currently playing
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
        self.crash_image = pygame.image.load("explosion3.png").convert_alpha() # Loads crash image

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

            if not self.thrust_sound_playing:
                 thrust_sound.play(-1)   # loop while held
                 self.thrust_sound_playing = True
        else:
            if self.thrust_sound_playing:
                thrust_sound.stop()
                self.thrust_sound_playing = False

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
                crash_rotated = pygame.transform.rotate(self.crash_image, self.angle)
                self.image = crash_rotated
                self.rect = self.image.get_rect(center=(self.x, self.y))
                explosion_sound.play()

    def draw(self):
        screen.blit(self.image, self.rect)#draw the spaceship image


# ----------------------------------------
# Ground class
# ----------------------------------------
class Ground:
    def __init__(self):
        # Load the ground image
        self.image = pygame.image.load("mars_ground.png").convert_alpha()
        # Scale it to fit the width of the screen and the height you want
        self.image = pygame.transform.scale(self.image, (WIDTH, 50))
        # Position the ground at the bottom of the screen
        self.rect = self.image.get_rect(topleft=(0, HEIGHT-50))

    def draw(self):
        screen.blit(self.image, self.rect)
        # Optional: keep landing pad rectangle
        pygame.draw.rect(screen, (150, 150, 150), (WIDTH//2-100, HEIGHT-55, 200, 10))
        
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

        if event.type == pygame.QUIT:
            running = False # Exit game if window is closed

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_q: 
                running = False # Quit game if Q is pressed

            if event.key == pygame.K_r:
                lander = Lander()
                game_state = PLAYING # Restart game if R is pressed

            if event.key ==pygame.K_p and game_state == PLAYING:
                game_state = PAUSED # Pause game if P is pressed
            elif event.key == pygame.K_p and game_state == PAUSED:
                game_state = PLAYING # Unpause game if P is pressed again

        if game_state == MENU:
            result = menu.handle_event(event)

            if result == "BEGIN":
                lander = Lander()
                game_state = PLAYING

            if result == "EXIT":
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

        thrust_sound.stop() # Stop thrust sound if it was playing

        if lander.landed:
            msg = font.render("SAFE LANDING!", True, GREEN)
        else:
            msg = font.render("CRASHED!", True, RED)

        msg_rect = msg.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)) # Center the message on the screen
        screen.blit(msg, msg_rect) # Draw the message on the screen

        quit_msg = font.render("Press Q to quit or R to restart", True, WHITE) # Instructions for quitting or restarting
        quit_rect = quit_msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)) # Center the instructions on the screen
        screen.blit(quit_msg, quit_rect) # Draw the instructions on the screen

    clock.tick(60) # Limit to 60 frames per second
    pygame.display.flip() # Update the display

pygame.quit() # Quit pygame
sys.exit() # Quit the game