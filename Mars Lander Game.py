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
SOURCE_FOLDER = os.path.dirname(os.path.abspath(__file__)) # Backup the current project folder by default
BACKUP_FOLDER = os.path.join(os.path.dirname(SOURCE_FOLDER), "Mars_Lander_Backups") # Keep backups outside source folder

def create_backup():
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Backup skipped: source folder not found: {SOURCE_FOLDER}")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Create a timestamp for the backup folder name
    backup_path = os.path.join(BACKUP_FOLDER, f"Assessment_3_Backup_{timestamp}") # Create a unique backup folder name using the timestamp

    try:
        os.makedirs(backup_path, exist_ok=True) # `exist_ok=True` prevents errors if the folder already exists
        shutil.copytree(SOURCE_FOLDER, backup_path, dirs_exist_ok=True) # Copy all files from source to backup
        print(f"Backup completed successfully! Files saved in: {backup_path}")
    except OSError as err:
        print(f"Backup skipped due to filesystem error: {err}")

create_backup()

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
# Level Settings
# ----------------------------------------
LEVELS = { # Define the settings for each level, including background and ground images, and landing pad position for the tutorial
    "TUTORIAL": {
        "background": "Tutorial_Background.png",
        "ground": "Tutorial_Ground.png",
        "landing_pad": {"x": WIDTH//2 - 100, "y": HEIGHT - 55, "width": 200, "height": 10}

    },
    "LEVEL_1": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "landing_pad": {"x": WIDTH//2 - 100, "y": HEIGHT - 55, "width": 200, "height": 10}

    },
    "LEVEL_2": {
        "background": "Level_2_Background.png",
        "ground": "Level_2_Ground.png"
    },
    "LEVEL_3": {
        "background": "Level_3_Background.png",
        "ground": "Level_3_Ground.png"
    },
    "LEVEL_4": {
        "background": "Level_4_Background.png",
        "ground": "Level_4_Ground.png"
    },
    "LEVEL_5": {
        "background": "Level_5_Background.png",
        "ground": "Level_5_Ground.png"
    }
}

# ----------------------------------------
# Colours
# ----------------------------------------
SKY = (255, 150, 100)
GROUND = (200, 80, 30)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
ORANGE = (204, 102, 0)
GREY = (107, 107, 107)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

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
def load_level_background(level_name): # Load the background image for the specified level
    level_data = LEVELS.get(level_name, LEVELS["LEVEL_1"])
    background_file = level_data["background"]

    image = pygame.image.load(background_file).convert()
    return pygame.transform.scale(image, (WIDTH, HEIGHT))

background_image = load_level_background("LEVEL_1")

# Load Sound Effects
thrust_sound = pygame.mixer.Sound("lander_thrust.mp3") # Load thrust sound effect
thrust_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound("lander_explode.wav")
menu_button_hover = pygame.mixer.Sound("menu_button_hover.wav")
menu_button_accept = pygame.mixer.Sound("menu_button_accept.wav")
menu_button_accept.set_volume(0.06)

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
            fill_colour = ORANGE            
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
        self.base_image = pygame.image.load("Lander.png").convert_alpha() # Loads lander image
        self.booster_image = pygame.image.load("Lander_Booster.png").convert_alpha() # Loads booster image
        self.boosterL_image = pygame.image.load("Lander_Booster_L.png").convert_alpha() # Loads left booster image
        self.boosterR_image = pygame.image.load("Lander_Booster_R.png").convert_alpha() # Loads right booster image
        self.crash_image = pygame.image.load("Lander_Explosion.png").convert_alpha() # Loads crash image

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Centers lander image on rectangle for positioning

    # --------------------
    # Tracking lander position
    # --------------------
    def update(self, gravity_scale=1.0, freeze_descent=False, landing_pad_rect=None):
        
        if freeze_descent:
            if self.thrust_sound_playing:
                thrust_sound.stop()
                self.thrust_sound_playing = False

        self.thrusting = False

        keys = pygame.key.get_pressed() # Checks which keys are currently pressed

        if not freeze_descent:
            self.speed_y += GRAVITY * gravity_scale # Gravity propels lander down

        # ----------
        # Controls
        # ----------
        if keys[pygame.K_SPACE] and self.fuel > 0 and not freeze_descent: # Check for space key press and fuel availability
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

        if freeze_descent:
            self.speed_y = 0
        else:
            self.y += self.speed_y

        self.x += self.speed_x

        # --------------------
        # Landing and crash detection
        # --------------------
        if self.y > HEIGHT - 100:
            self.y = HEIGHT - 100
            self.rect.center = (self.x, self.y)
            on_landing_pad = True
            if landing_pad_rect is not None:
                on_landing_pad = landing_pad_rect.collidepoint(self.rect.centerx, landing_pad_rect.centery) # Check if the lander is within the landing pad area

            if on_landing_pad and abs(self.speed_y) <= SAFE_SPEED and abs(self.angle) <= 12:
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
    def __init__(self, level_name="LEVEL_1"):
        level_data = LEVELS.get(level_name, LEVELS["LEVEL_1"])
        ground_file = level_data["ground"]
        pad_data = level_data.get("landing_pad", LEVELS["LEVEL_1"]["landing_pad"])

        if not os.path.exists(ground_file):
            ground_file = LEVELS["LEVEL_1"]["ground"] # Fallback ground for missing level files
        # Load the ground image
        self.image = pygame.image.load(ground_file).convert_alpha()
        # Scale it to fit the width of the screen and the height you want
        self.image = pygame.transform.scale(self.image, (WIDTH, 50))
        # Position the ground at the bottom of the screen
        self.rect = self.image.get_rect(topleft=(0, HEIGHT-50))
        self.landing_pad_rect = pygame.Rect(
            pad_data["x"],
            pad_data["y"],
            pad_data["width"],
            pad_data["height"]
        )

    def draw(self):
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, WHITE, self.landing_pad_rect) # Draw the landing pad as a white rectangle on top of the ground      

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
# Tutorial Guide Class
# ----------------------------------------
class TutorialGuide: # Provides on-screen instructions and controls the tutorial flow
    def __init__(self):
        self.title_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 34)
        self.tip_colour = (20, 20, 20)
        self.box_colour = (255, 255, 255)
        self.turn_intro_shown = False
        self.turn_intro_frames = 75
        self.turn_intro_frames_remaining = self.turn_intro_frames
        self.current_step_index = None
        self.completed_steps = set()

    def get_steps(self, lander): # Define the tutorial steps and their completion conditions
            return [
                {
                    "title": "Use Main Thruster",
                    "tip": "Hold SPACE to fire the main thruster.",
                    "done": lander.fuel < START_FUEL # Check if fuel has been used, indicating the main thruster has been fired
                },
                {
                    "title": "Learn to Turn",
                    "tip": "Use LEFT and RIGHT arrows to rotate the lander.",
                    "done": abs(lander.angle) > 0 # Check if the lander has been rotated, indicating the turn controls have been used
                }
            ]

    def get_step_states(self, lander): # Get the current state of each tutorial step, marking them as done if their conditions are met or if they were previously completed
        steps = self.get_steps(lander)
        states = []
        for index, step in enumerate(steps): # Mark steps as done if their conditions are met or if they were previously completed
            done = step["done"] or index in self.completed_steps
            states.append({"title": step["title"], "tip": step["tip"], "done": done})
        return states

    def update(self, lander):
        if not lander.alive or lander.landed:
            return {"freeze_descent": False, "gravity_scale": 0.5}

        steps = self.get_step_states(lander)

        for index, step in enumerate(steps):
            if step["done"]:
                self.completed_steps.add(index)

        next_step_index = len(steps)
        for index, step in enumerate(steps):
            if not step["done"]:
                next_step_index = index
                break

        self.current_step_index = next_step_index

        turn_step_active = self.current_step_index == 1 and 0 in self.completed_steps and 1 not in self.completed_steps
        if turn_step_active and not self.turn_intro_shown:
            self.turn_intro_frames_remaining -= 1
            freeze_descent = self.turn_intro_frames_remaining > 0
            if self.turn_intro_frames_remaining <= 0:
                self.turn_intro_shown = True
        else:
            freeze_descent = False

        return {"freeze_descent": freeze_descent, "gravity_scale": 0.5}
    def draw(self, lander):
        if not lander.alive or lander.landed:
            return

        steps = self.get_step_states(lander)
        active_step = None
        
        if self.current_step_index is not None and self.current_step_index < len(steps):
            active_step = steps[self.current_step_index]
        else:
            for step in steps:
                if not step["done"]:
                    active_step = step
                    break

        if active_step is None:
            active_step = {
                "title": "Tutorial Complete",
                "tip": "Great work! Finish the landing to continue.",
                "done": True
            }

        panel = pygame.Rect(120, 20, WIDTH - 240, 90)
        pygame.draw.rect(screen, self.box_colour, panel, border_radius=12)
        pygame.draw.rect(screen, BLACK, panel, 3, border_radius=12)

        title_text = self.title_font.render(active_step["title"], True, self.tip_colour)
        tip_text = self.text_font.render(active_step["tip"], True, self.tip_colour)
        screen.blit(title_text, (panel.x + 20, panel.y + 12))
        screen.blit(tip_text, (panel.x + 20, panel.y + 52))

# ----------------------------------------
# Game Objects
# ----------------------------------------
def start_level(level_name):
    global lander, ground, background_image, game_state, current_level, tutorial_guide
    current_level = level_name
    lander = Lander()
    ground = Ground(level_name)
    background_image = load_level_background(level_name)
    tutorial_guide = TutorialGuide() if level_name == "TUTORIAL" else None
    game_state = PLAYING

lander = None # Lander
current_level = "LEVEL_1"
ground = Ground(current_level) # Mars ground
hud = HUD() # Information display
menu = Menu() # Start menu
tutorial_guide = None

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
                start_level(current_level) # Restart current level if R is pressed

            if event.key ==pygame.K_p and game_state == PLAYING:
                game_state = PAUSED # Pause game if P is pressed
            elif event.key == pygame.K_p and game_state == PAUSED:
                game_state = PLAYING # Unpause game if P is pressed again

        if game_state == MENU:
            result = menu.handle_event(event)

            if result == "BEGIN":
                 start_level("LEVEL_1")

            if result == "TUTORIAL":
                start_level("TUTORIAL")

            if result == "EXIT":
                running = False

    # ----------
    # Updating Game
    # ----------
    if game_state == PLAYING:
        tutorial_settings = {"freeze_descent": False, "gravity_scale": 1.0}
        if tutorial_guide is not None and current_level == "TUTORIAL":
            tutorial_settings = tutorial_guide.update(lander)

        lander.update(
            gravity_scale=tutorial_settings["gravity_scale"],
            freeze_descent=tutorial_settings["freeze_descent"],
            landing_pad_rect=ground.landing_pad_rect
        ) # Update lander position and state

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
        if current_level != "TUTORIAL":
            hud.draw(lander) # Draw the HUD
        if tutorial_guide is not None and current_level == "TUTORIAL":
            tutorial_guide.draw(lander)

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