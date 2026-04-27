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
GRAVITY = 0.06 # slower descent for more controlled falling
THRUST = 0.16 # weaker boosters for finer movement
START_FUEL = 500 # starting amount of fuel
SAFE_SPEED = 3 # maximum safe landing speed
LANDER_SCALE = 0.45 # scale factor for the lander image size
ZOOM_NEAR_DISTANCE = 180 # distance where camera reaches max zoom
ZOOM_FAR_DISTANCE = 420 # distance where camera is fully zoomed out
MIN_ZOOM = 1.0
MAX_ZOOM = 1.8

# ----------------------------------------
# Level Settings
# ----------------------------------------
LEVELS = {
    "TUTORIAL": {
        "background": "Tutorial_Background.png",
        "ground": "Tutorial_Ground.png",
        "terrain_points": [
            (0, 700), (1200, 700)
        ],
        "landing_pad_x": WIDTH//2 - 60,
        "landing_pad": {"x": WIDTH//2 - 60, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_1": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "terrain_points": [
            (0, 700), (300, 700), (400, 670), (500, 700),
            (540, 700), (660, 700),  # flat landing pad zone
            (700, 700), (1200, 700)
        ],
        "landing_pad_x": 540,
        "landing_pad": {"x": 540, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_2": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "terrain_points": [
            (0, 700), (150, 660), (300, 700), (420, 640),
            (500, 700), (560, 700),  # flat landing pad zone
            (620, 700), (800, 650), (1000, 690), (1200, 700)
        ],
        "landing_pad_x": 500,
        "landing_pad": {"x": 500, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_3": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "terrain_points": [
            (0, 700), (100, 620), (250, 680), (350, 600),
            (460, 700), (540, 700),  # flat landing pad zone
            (600, 700), (750, 610), (900, 670), (1100, 630), (1200, 700)
        ],
        "landing_pad_x": 460,
        "landing_pad": {"x": 460, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_4": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "terrain_points": [
            (0, 700), (80, 580), (200, 660), (320, 570),
            (420, 700), (500, 700),  # flat landing pad zone (narrower)
            (560, 700), (680, 580), (800, 650), (950, 560), (1200, 700)
        ],
        "landing_pad_x": 420,
        "landing_pad": {"x": 420, "y": HEIGHT - 55, "width": 80, "height": 8}
    },
    "LEVEL_5": {
        "background": "Level_1_Background.png",
        "ground": "Level_1_Ground.png",
        "terrain_points": [
            (0, 700), (60, 550), (150, 630), (250, 530),
            (370, 700), (430, 700),  # flat landing pad zone (narrowest)
            (490, 700), (600, 540), (720, 620), (850, 510), (1000, 640), (1200, 700)
        ],
        "landing_pad_x": 370,
        "landing_pad": {"x": 370, "y": HEIGHT - 55, "width": 60, "height": 8}
    }
}

# ----------------------------------------
# Level Progression System
# ----------------------------------------
LEVEL_ORDER = ["LEVEL_1", "LEVEL_2", "LEVEL_3", "LEVEL_4", "LEVEL_5"]  # Defines the order levels are played in
current_level_index = 0  # Tracks which level the player is currently on
completed_levels = set()  # Tracks which levels the player has completed

def get_terrain_y(terrain_points, x):
    """Interpolate terrain height at a given x position."""
    for i in range(len(terrain_points) - 1):
        x1, y1 = terrain_points[i]
        x2, y2 = terrain_points[i + 1]
        if x1 <= x <= x2:
            t = (x - x1) / (x2 - x1)
            return y1 + t * (y2 - y1)
    return HEIGHT - 50  # fallback if x is out of bounds

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
menu_background = pygame.image.load("Menu_Background.png").convert() # Load menu background image
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT)) # Scale menu background to fit screen
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
        start_y = HEIGHT - self.margin_y - (self.button_height * 4 + self.spacing * 3)

        # Button rectangles
        self.buttons = [
            Button(self.margin_x, start_y, self.button_width, self.button_height, "Tutorial", "TUTORIAL"),
            Button(self.margin_x, start_y + self.button_height + self.spacing, self.button_width, self.button_height, "Levels", "LEVELS"),
            Button(self.margin_x, start_y + (self.button_height + self.spacing) * 2, self.button_width, self.button_height, "Begin", "BEGIN"),
            Button(self.margin_x, start_y + (self.button_height + self.spacing) * 3, self.button_width, self.button_height, "Exit", "EXIT")
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
        if level_scroller.visible:
            return

        screen.blit(menu_background, (0,0))

        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event):
        for button in self.buttons:
            action = button.handle_event(event)
            if action:
                menu_button_accept.play() # Play accept sound when a button is clicked
                return action

# ----------------------------------------
# Level Scroller Class
# ----------------------------------------
class LevelScroller:
    def __init__(self):
        self.visible = False
        self.card_width = 160
        self.card_height = 100
        self.card_spacing = 20
        self.scroll_offset = 0

        self.title_font = pygame.font.Font(None, 38)
        self.label_font = pygame.font.Font(None, 34)
        self.scroll_speed = 18
        self.hovered_card = None

        # CENTRED PANEL (NEW)
        panel_width = WIDTH - 200
        panel_height = 260

        self.panel_rect = pygame.Rect(
            (WIDTH - panel_width) // 2,
            (HEIGHT - panel_height) // 2,
            panel_width,
            panel_height
        )

        # RETURN BUTTON (NEW)
        self.button_width = 220
        self.button_height = 60

        self.return_button = Button(
            (WIDTH - self.button_width) // 2,
            self.panel_rect.bottom + 25,
            self.button_width,
            self.button_height,
            "Return to Menu",
            "MENU_RETURN"
        )

    def toggle(self):
        self.visible = not self.visible

    def _total_content_width(self):
        return len(LEVEL_ORDER) * (self.card_width + self.card_spacing) - self.card_spacing

    def _max_scroll(self):
        visible_width = self.panel_rect.width - 40  # 20px padding each side
        return max(0, self._total_content_width() - visible_width)

    def _is_unlocked(self, level_name):
        idx = LEVEL_ORDER.index(level_name)
        if idx == 0:
            return True  # first level always unlocked
        return LEVEL_ORDER[idx - 1] in completed_levels

    def draw(self, surface):
        if not self.visible:
            return

        # Panel background
        pygame.draw.rect(surface, BLACK, self.panel_rect, border_radius=12)
        pygame.draw.rect(surface, ORANGE, self.panel_rect, 3, border_radius=12)

        title = self.title_font.render("Select Level", True, WHITE)
        surface.blit(title, (self.panel_rect.x + 20, self.panel_rect.y + 14))

        # Clip cards to panel area
        clip_rect = pygame.Rect(
            self.panel_rect.x + 10,
            self.panel_rect.y + 55,
            self.panel_rect.width - 20,
            self.card_height + 10
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        self.hovered_card = None
        mouse_pos = pygame.mouse.get_pos()

        for i, level_name in enumerate(LEVEL_ORDER):
            card_x = (self.panel_rect.x + 20) + i * (self.card_width + self.card_spacing) - self.scroll_offset
            card_y = self.panel_rect.y + 58
            card_rect = pygame.Rect(card_x, card_y, self.card_width, self.card_height)

            unlocked = self._is_unlocked(level_name)
            done = level_name in completed_levels
            hovered = card_rect.collidepoint(mouse_pos) and unlocked and clip_rect.collidepoint(mouse_pos)

            if hovered:
                self.hovered_card = level_name

            # Card colour
            if done:
                fill = (0, 120, 40) if not hovered else (0, 160, 55)
            elif unlocked:
                fill = (60, 60, 60) if not hovered else ORANGE
            else:
                fill = (30, 30, 30)  # locked

            pygame.draw.rect(surface, fill, card_rect, border_radius=10)
            border_colour = WHITE if done else (GREY if not hovered else ORANGE)
            pygame.draw.rect(surface, border_colour, card_rect, 2, border_radius=10)

            # Label
            display = level_name.replace("LEVEL_", "Level ")
            label = self.label_font.render(display, True, WHITE if unlocked else GREY)
            label_rect = label.get_rect(center=(card_rect.centerx, card_rect.centery - 10))
            surface.blit(label, label_rect)

            # Status tag
            if done:
                tag = self.label_font.render("Done", True, (180, 255, 180))
            elif unlocked:
                tag = self.label_font.render("Play", True, (220, 220, 220))
            else:
                tag = self.label_font.render("Locked", True, (120, 120, 120))
            tag_rect = tag.get_rect(center=(card_rect.centerx, card_rect.centery + 22))
            surface.blit(tag, tag_rect)

        surface.set_clip(old_clip)
        self.return_button.draw(surface)

        # Scroll arrows
        if self.scroll_offset > 0:
            pygame.draw.polygon(surface, WHITE, [
                (self.panel_rect.x + 8, self.panel_rect.centery + 20),
                (self.panel_rect.x + 22, self.panel_rect.centery + 8),
                (self.panel_rect.x + 22, self.panel_rect.centery + 32)
            ])
        if self.scroll_offset < self._max_scroll():
            rx = self.panel_rect.right
            pygame.draw.polygon(surface, WHITE, [
                (rx - 8, self.panel_rect.centery + 20),
                (rx - 22, self.panel_rect.centery + 8),
                (rx - 22, self.panel_rect.centery + 32)
            ])

    def handle_event(self, event):
        if not self.visible:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed * 3)
            if event.key == pygame.K_RIGHT:
                self.scroll_offset = min(self._max_scroll(), self.scroll_offset + self.scroll_speed * 3)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed)
            if event.button == 5:
                self.scroll_offset = min(self._max_scroll(), self.scroll_offset + self.scroll_speed)

            # IMPORTANT: return button check (FIX)
            action = self.return_button.handle_event(event)
            if action:
                menu_button_accept.play()
                return action

            # level selection click
            if event.button == 1 and self.hovered_card:
                menu_button_accept.play()
                return self.hovered_card

        return None

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
        self.base_image = self.scale_lander_image(pygame.image.load("Lander.png").convert_alpha()) # Loads lander image
        self.booster_image = self.scale_lander_image(pygame.image.load("Lander_Booster.png").convert_alpha()) # Loads booster image
        self.boosterL_image = self.scale_lander_image(pygame.image.load("Lander_Booster_L.png").convert_alpha()) # Loads left booster image
        self.boosterR_image = self.scale_lander_image(pygame.image.load("Lander_Booster_R.png").convert_alpha()) # Loads right booster image
        self.crash_image = self.scale_lander_image(pygame.image.load("Lander_Explosion.png").convert_alpha()) # Loads crash image

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Centers lander image on rectangle for positioning

    def scale_lander_image(self, image): # Scales the lander image based on the defined LANDER_SCALE factor
        width = int(image.get_width() * LANDER_SCALE)
        height = int(image.get_height() * LANDER_SCALE)
        return pygame.transform.smoothscale(image, (width, height))
    
    def get_collision_rect(self): # Get a smaller collision rectangle for more forgiving landing and crash detection
        collision_rect = self.rect.inflate(-self.rect.width * 0.45, -self.rect.height * 0.35)
        collision_rect.y += int(self.rect.height * 0.12) # bias collision zone toward landing legs
        return collision_rect

    # --------------------
    # Tracking lander position
    # --------------------
    def update(self, gravity_scale=1.0, freeze_descent=False, landing_pad_rect=None, terrain_points=None):
        
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
            self.angle += 1.5 # Slower turning for precision
            self.image = self.boosterL_image

        if keys[pygame.K_RIGHT]:
            self.angle -= 2.5
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
        collision_rect = self.get_collision_rect()
        ground_top = get_terrain_y(terrain_points, collision_rect.centerx) if terrain_points else HEIGHT - 50
        collision_rect = self.get_collision_rect()
        over_landing_pad = False
        landing_surface_top = ground_top
        if landing_pad_rect is not None:
            over_landing_pad = (
                landing_pad_rect.left <= collision_rect.centerx <= landing_pad_rect.right
            )
            if over_landing_pad:
                landing_surface_top = min(ground_top, landing_pad_rect.top)

        if collision_rect.bottom >= landing_surface_top:
            penetration = collision_rect.bottom - landing_surface_top
            self.y -= penetration
            self.rect = self.image.get_rect(center=(self.x, self.y))
            collision_rect = self.get_collision_rect()
            on_landing_pad = (
                landing_pad_rect is not None
                and over_landing_pad
                and abs(collision_rect.bottom - landing_pad_rect.top) <= 2
            )
            if on_landing_pad and abs(self.speed_y) <= SAFE_SPEED and abs(self.angle) <= 12: # Check for safe landing conditions
                self.landed = True

            else: # If not landed safely, it's a crash
                self.alive = False
                crash_rotated = pygame.transform.rotate(self.crash_image, self.angle)
                self.image = crash_rotated
                self.rect = self.image.get_rect(center=(self.x, self.y))
                explosion_sound.play()

    def draw(self, surface):
        surface.blit(self.image, self.rect)#draw the spaceship image at its current position and orientation

# ----------------------------------------
# Ground class
# ----------------------------------------
class Ground:
    def __init__(self, level_name="LEVEL_1"):
        self.level_name = level_name
        level_data = LEVELS.get(level_name, LEVELS["LEVEL_1"])
        ground_file = level_data["ground"]
        pad_data = level_data.get("landing_pad", LEVELS["LEVEL_1"]["landing_pad"])
        self.terrain_points = level_data.get("terrain_points", [(0, 700), (1200, 700)])

        if not os.path.exists(ground_file):
            ground_file = LEVELS["LEVEL_1"]["ground"]

        self.image = pygame.image.load(ground_file).convert_alpha()
        self.image = pygame.transform.scale(self.image, (WIDTH, 50))
        self.rect = self.image.get_rect(topleft=(0, HEIGHT - 50))

        self.landing_pad_rect = pygame.Rect(
            pad_data["x"],
            pad_data["y"],
            pad_data["width"],
            pad_data["height"]
        )

    def draw(self, surface):
        # Build a filled polygon from terrain points down to the bottom of screen
        poly_points = list(self.terrain_points)
        poly_points.append((self.terrain_points[-1][0], HEIGHT))
        poly_points.append((self.terrain_points[0][0], HEIGHT))

        if self.level_name == "TUTORIAL":
            ground_colour = (235, 235, 235)  # slightly darker than pure white for visibility
            edge_colour = (200, 200, 200)    # darker outline so landing pad stands out
        else:
            ground_colour = GROUND
            edge_colour = (180, 60, 10)

        pygame.draw.polygon(surface, ground_colour, poly_points)
        pygame.draw.lines(surface, edge_colour, False, self.terrain_points, 3)

        pygame.draw.rect(surface, WHITE, self.landing_pad_rect)

# ----------------------------------------
# HUD Class
# ----------------------------------------
class HUD:
    def draw(self, lander, surface):
        altitude = HEIGHT - 100 - lander.y

        texts = [
            f"Altitude: {int(altitude)}",
            f"Vertical Speed: {lander.speed_y:.1f}",
        ]

        for i, text in enumerate(texts):
            msg = font.render(text, True, WHITE)
            surface.blit(msg, (20, 20 + i * 50))

    def draw_level_name(self, level_name, surface):
        if level_name.startswith("LEVEL_"):
            display_name = level_name.replace("LEVEL_", "Level ")
        else:
            display_name = level_name.capitalize()

        msg = font.render(display_name, True, WHITE)
        rect = msg.get_rect(center=(WIDTH // 2, 20))
        surface.blit(msg, rect)

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
    def draw(self, lander, surface):
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
        pygame.draw.rect(surface, self.box_colour, panel, border_radius=12)
        pygame.draw.rect(surface, BLACK, panel, 3, border_radius=12)

        title_text = self.title_font.render(active_step["title"], True, self.tip_colour)
        tip_text = self.text_font.render(active_step["tip"], True, self.tip_colour)
        surface.blit(title_text, (panel.x + 20, panel.y + 12))
        surface.blit(tip_text, (panel.x + 20, panel.y + 52))


# ----------------------------------------
# Camera Zoom Functions
# ----------------------------------------
def get_zoom(lander, landing_pad_rect):
    pad_center_x = landing_pad_rect.centerx
    pad_center_y = landing_pad_rect.centery
    distance = math.hypot(lander.x - pad_center_x, lander.y - pad_center_y)

    return MAX_ZOOM if distance <= ZOOM_NEAR_DISTANCE else MIN_ZOOM # Zoom in when close to landing pad, zoom out when far away

def draw_zoomed_scene(scene_surface, zoom, focus_x, focus_y):
    if zoom <= 1.0:
        screen.blit(scene_surface, (0, 0))
        return

    scaled_width = int(WIDTH * zoom)
    scaled_height = int(HEIGHT * zoom)
    scaled_scene = pygame.transform.smoothscale(scene_surface, (scaled_width, scaled_height))

    scaled_focus_x = focus_x * zoom
    scaled_focus_y = focus_y * zoom

    left = int(max(0, min(scaled_width - WIDTH, scaled_focus_x - WIDTH / 2)))
    top = int(max(0, min(scaled_height - HEIGHT, scaled_focus_y - HEIGHT / 2)))

    screen.blit(scaled_scene, (0, 0), area=pygame.Rect(left, top, WIDTH, HEIGHT))

# ----------------------------------------
# Game Objects
# ----------------------------------------
def start_level(level_name):
    global lander, ground, background_image, game_state
    global current_level, tutorial_guide, current_level_index

    current_level = level_name

    # Only set index for real levels (NOT tutorial)
    if level_name in LEVEL_ORDER:
        current_level_index = LEVEL_ORDER.index(level_name)

    lander = Lander()
    ground = Ground(level_name)
    background_image = load_level_background(level_name)

    tutorial_guide = TutorialGuide() if level_name == "TUTORIAL" else None

    game_state = PLAYING

def return_to_menu():
    global game_state, tutorial_guide, level_scroller

    thrust_sound.stop()
    tutorial_guide = None

    level_scroller.visible = False
    level_scroller.scroll_offset = 0
    
    game_state = MENU

def go_to_next_level():
    global current_level_index, current_level, completed_levels

    if current_level == "TUTORIAL":
        return_to_menu()
        return

    # Mark current level as completed
    completed_levels.add(current_level)

    if current_level_index < len(LEVEL_ORDER) - 1:
        current_level_index += 1
        next_level = LEVEL_ORDER[current_level_index]
        start_level(next_level)
    else:
        return_to_menu()

lander = None # Lander
current_level = "LEVEL_1"
ground = Ground(current_level) # Mars ground
hud = HUD() # Information display
menu = Menu() # Start menu
level_scroller = LevelScroller()
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
            if event.key == pygame.K_m:
                return_to_menu()
                continue


            if event.key == pygame.K_q: 
                running = False # Quit game if Q is pressed

            if event.key == pygame.K_r:
                start_level(current_level) # Restart current level if R is pressed

            if event.key ==pygame.K_p and game_state == PLAYING:
                game_state = PAUSED # Pause game if P is pressed
            elif event.key == pygame.K_p and game_state == PAUSED:
                game_state = PLAYING # Unpause game if P is pressed again

            if game_state == ENDED:
                if event.key == pygame.K_SPACE:
                    if current_level == "TUTORIAL":
                        return_to_menu()
                    else:
                        if lander.landed:
                            go_to_next_level()

        if game_state == MENU:

            result = None
            scroller_result = None

            # Level scroller gets priority if visible
            if level_scroller.visible:
                scroller_result = level_scroller.handle_event(event)
            else:
                result = menu.handle_event(event)

            if scroller_result == "MENU_RETURN":
                return_to_menu()

            elif scroller_result in LEVEL_ORDER:
                current_level_index = LEVEL_ORDER.index(scroller_result)
                start_level(scroller_result)

            if result == "BEGIN":
                current_level_index = 0
                level_scroller.visible = False
                start_level(LEVEL_ORDER[0])

            if result == "LEVELS":
                level_scroller.toggle()
                menu_button_accept.play()

            if result == "TUTORIAL":
                current_level_index = 0
                current_level = "TUTORIAL"
                level_scroller.visible = False
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
            landing_pad_rect=ground.landing_pad_rect,
            terrain_points=ground.terrain_points
        )

        if lander.landed or not lander.alive:
            game_state = ENDED

            # prevent tutorial from accidentally entering level progression logic
            if current_level == "TUTORIAL":
                current_level_index = 0

            # prevent tutorial from triggering level progression
            if current_level == "TUTORIAL":
                current_level_index = 0

    # ----------
    # Drawing Everything
    # ----------
    if game_state == MENU:
        if level_scroller.visible:
            level_scroller.draw(screen)
        else:
            menu.draw()
        
    else:
        scene_surface = pygame.Surface((WIDTH, HEIGHT))
        scene_surface.blit(background_image, (0, 0)) # Draw background image
        ground.draw(scene_surface) # Draw the ground
        lander.draw(scene_surface) # Draw the lander

        camera_zoom = get_zoom(lander, ground.landing_pad_rect)
        camera_focus_x = (lander.x + ground.landing_pad_rect.centerx) / 2
        camera_focus_y = (lander.y + ground.landing_pad_rect.centery) / 2
        draw_zoomed_scene(scene_surface, camera_zoom, camera_focus_x, camera_focus_y)

        hud_hidden_for_zoom = camera_zoom > MIN_ZOOM # Hide HUD when zoomed in to prevent clutter and maintain focus on landing
        if not hud_hidden_for_zoom:
            if current_level != "TUTORIAL":
                hud.draw_level_name(current_level, screen)

        if current_level != "TUTORIAL" and not hud_hidden_for_zoom:
            hud.draw(lander, screen)

        if tutorial_guide is not None and current_level == "TUTORIAL" and not hud_hidden_for_zoom:
            tutorial_guide.draw(lander, screen)

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

            # Show different instructions depending on outcome
            if lander.landed:
                quit_msg = font.render("Press SPACE for next level, R to retry, M for menu, or Q to quit", True, WHITE)
            else:
                quit_msg = font.render("Press R to retry or M for menu", True, WHITE)

            quit_rect = quit_msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            screen.blit(quit_msg, quit_rect)

    clock.tick(60) # Limit to 60 frames per second
    pygame.display.flip() # Update the display

pygame.quit() # Quit pygame
sys.exit() # Quit the game