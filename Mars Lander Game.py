# ----------------------------------------
# imported libraries
# ----------------------------------------
import pygame
import sys 
import math 
import os
import json
import shutil
import datetime
import random

# ----------------------------------------
# backup procedures
# ----------------------------------------
# grab the folder where this script lives
SOURCE_FOLDER = os.path.dirname(os.path.abspath(__file__))
# put backups one level up from the game folder
BACKUP_FOLDER = os.path.join(os.path.dirname(SOURCE_FOLDER), "Mars_Lander_Backups")

def create_backup():
    # skip the backup if the source folder somehow doesn't exist
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Backup skipped: source folder not found: {SOURCE_FOLDER}")
        return
    # use the current time so every backup gets a unique folder name
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(BACKUP_FOLDER, f"Assessment_3_Backup_{timestamp}")
    try:
        os.makedirs(backup_path, exist_ok=True)
        shutil.copytree(SOURCE_FOLDER, backup_path, dirs_exist_ok=True)
        print(f"Backup completed successfully! Files saved in: {backup_path}")
    except OSError as err:
        # filesystem errors shouldn't crash the game, just warn and move on
        print(f"Backup skipped due to filesystem error: {err}")

create_backup()

# ----------------------------------------
# game states
# ----------------------------------------
MENU = 'MENU'
PLAYING = 'PLAYING'
ENDED = 'ENDED'
PAUSED = 'PAUSED'

# ----------------------------------------
# constants
# ----------------------------------------
WIDTH = 1200
HEIGHT = 750
GRAVITY = 0.04
THRUST = 0.12
START_FUEL = 500
SAFE_SPEED = 3       # max vertical speed allowed for a safe touchdown
LANDER_SCALE = 0.45  # how much to shrink the lander sprite
ZOOM_NEAR_DISTANCE = 180   # camera zooms in when lander is this close to the pad
ZOOM_FAR_DISTANCE = 420    # camera zooms back out beyond this distance
MIN_ZOOM = 1.0
MAX_ZOOM = 1.8

# screen shake constants
SHAKE_DURATION = 12      # frames of shake after crash
SHAKE_MAGNITUDE = 4      # max pixel offset

# wind constants — only applied in levels 4 and 5
WIND_LEVELS = {"LEVEL_4", "LEVEL_5"}
WIND_FORCE_LEVEL_4 = 0.018   # moderate wind
WIND_FORCE_LEVEL_5 = 0.032   # stronger, more variable wind

# ----------------------------------------
# persistent save helpers
# ----------------------------------------
# save file sits next to this script so it's easy to find
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mars_lander_save.json")

def load_save():
    # try to read the save file; return safe defaults if anything goes wrong
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        # fill in any keys that older save files might be missing
        data.setdefault("completed_levels", [])
        data.setdefault("best_scores", {})
        return data
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {"completed_levels": [], "best_scores": {}}

def write_save(completed_levels_set, best_scores_dict):
    # convert the set to a list so it's JSON-serialisable
    data = {
        "completed_levels": list(completed_levels_set),
        "best_scores": best_scores_dict
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as err:
        print(f"Save failed: {err}")

# load save data at startup
_save = load_save()
completed_levels = set(_save["completed_levels"])
best_scores = _save["best_scores"]   # dict: level_name -> int score

# ----------------------------------------
# level settings
# ----------------------------------------
LEVELS = {
    "TUTORIAL": {
        "background": "Tutorial_Background.png",
        # completely flat ground for the tutorial
        "terrain_points": [
            (0, 700), (1200, 700)
        ],
        "landing_pad_x": WIDTH//2 - 60,
        "landing_pad": {"x": WIDTH//2 - 60, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_1": {
        "background": "Level_1_Background.png",
        # gentle bumps to introduce terrain without being too punishing
        "terrain_points": [
            (0, 700), (300, 700), (400, 670), (500, 700),
            (540, 700), (660, 700),
            (700, 700), (1200, 700)
        ],
        "landing_pad_x": 540,
        "landing_pad": {"x": 540, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_2": {
        "background": "Level_1_Background.png",
        # slightly more varied terrain
        "terrain_points": [
            (0, 700), (150, 660), (300, 700), (420, 640),
            (500, 700), (560, 700),
            (620, 700), (800, 650), (1000, 690), (1200, 700)
        ],
        "landing_pad_x": 500,
        "landing_pad": {"x": 500, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_3": {
        "background": "Level_1_Background.png",
        # peaks are taller here, need to watch descent angle more carefully
        "terrain_points": [
            (0, 700), (100, 620), (250, 680), (350, 600),
            (460, 700), (540, 700),
            (600, 700), (750, 610), (900, 670), (1100, 630), (1200, 700)
        ],
        "landing_pad_x": 460,
        "landing_pad": {"x": 460, "y": HEIGHT - 55, "width": 120, "height": 8}
    },
    "LEVEL_4": {
        "background": "Level_1_Background.png",
        # narrower pad and wind force kicks in on this level
        "terrain_points": [
            (0, 700), (80, 580), (200, 660), (320, 570),
            (420, 700), (500, 700),
            (560, 700), (680, 580), (800, 650), (950, 560), (1200, 700)
        ],
        "landing_pad_x": 420,
        "landing_pad": {"x": 420, "y": HEIGHT - 55, "width": 80, "height": 8}
    },
    "LEVEL_5": {
        "background": "Level_1_Background.png",
        # very narrow pad, jagged terrain, and gusty unpredictable wind
        "terrain_points": [
            (0, 700), (60, 550), (150, 630), (250, 530),
            (370, 700), (430, 700),
            (490, 700), (600, 540), (720, 620), (850, 510), (1000, 640), (1200, 700)
        ],
        "landing_pad_x": 370,
        "landing_pad": {"x": 370, "y": HEIGHT - 55, "width": 60, "height": 8}
    }
}

# ----------------------------------------
# level progression system
# ----------------------------------------
LEVEL_ORDER = ["LEVEL_1", "LEVEL_2", "LEVEL_3", "LEVEL_4", "LEVEL_5"]
current_level_index = 0

# work out the terrain height at any given horizontal position using linear interpolation
def get_terrain_y(terrain_points, x):
    for i in range(len(terrain_points) - 1):
        x1, y1 = terrain_points[i]
        x2, y2 = terrain_points[i + 1]
        if x1 <= x <= x2:
            t = (x - x1) / (x2 - x1)
            return y1 + t * (y2 - y1)
    return HEIGHT - 50

# ----------------------------------------
# colours
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
CYAN = (0, 220, 255)

# ----------------------------------------
# pygame setup
# ----------------------------------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mars Lander")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 34)

# ----------------------------------------
# background image loading
# ----------------------------------------
menu_background = pygame.image.load("Menu_Background.png").convert()
menu_background = pygame.transform.scale(menu_background, (WIDTH, HEIGHT))

def load_level_background(level_name):
    # look up which image file this level uses, fall back to level 1 if not found
    level_data = LEVELS.get(level_name, LEVELS["LEVEL_1"])
    background_file = level_data["background"]
    image = pygame.image.load(background_file).convert()
    return pygame.transform.scale(image, (WIDTH, HEIGHT))

background_image = load_level_background("LEVEL_1")

# ----------------------------------------
# sound loading
# ----------------------------------------
thrust_sound = pygame.mixer.Sound("lander_thrust.mp3")
thrust_sound.set_volume(0.5)
explosion_sound = pygame.mixer.Sound("lander_explode.wav")
menu_button_hover = pygame.mixer.Sound("menu_button_hover.wav")
menu_button_accept = pygame.mixer.Sound("menu_button_accept.wav")
menu_button_accept.set_volume(0.06)

# ----------------------------------------
# score system
# ----------------------------------------
def calculate_score(fuel_remaining, elapsed_time_seconds, landed):
    # crashed landings get zero points
    if not landed:
        return 0
    # reward conserving fuel and landing quickly; always add a flat landing bonus
    fuel_score = int((fuel_remaining / START_FUEL) * 500)
    time_score = max(0, int(300 - elapsed_time_seconds * 2))
    landing_bonus = 200
    return fuel_score + time_score + landing_bonus

# ----------------------------------------
# button class
# ----------------------------------------
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.font = pygame.font.Font(None, 40)
        # track hover state so the hover sound only plays on entry, not every frame
        self.hovered_last_frame = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)

        # play the hover sound once when the mouse first moves over the button
        if hovered and not self.hovered_last_frame:
            menu_button_hover.play()
        self.hovered_last_frame = hovered

        fill_colour   = ORANGE if hovered else BLACK
        outline_colour = BLACK  if hovered else GREY
        text_colour    = BLACK  if hovered else GREY

        pygame.draw.rect(surface, fill_colour, self.rect)
        pygame.draw.rect(surface, outline_colour, self.rect, 3)

        label = self.font.render(self.text, True, text_colour)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def handle_event(self, event):
        # return the button's action string when clicked, otherwise nothing
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return self.action

# ----------------------------------------
# menu class
# ----------------------------------------
class Menu:
    def __init__(self):
        self.button_width = 260
        self.button_height = 75
        self.spacing = 20
        self.margin_x = 50
        self.margin_y = 50

        # anchor the stack of buttons to the bottom-left corner
        start_y = HEIGHT - self.margin_y - (self.button_height * 4 + self.spacing * 3)

        self.buttons = [
            Button(self.margin_x, start_y, self.button_width, self.button_height, "Tutorial", "TUTORIAL"),
            Button(self.margin_x, start_y + self.button_height + self.spacing, self.button_width, self.button_height, "Levels", "LEVELS"),
            Button(self.margin_x, start_y + (self.button_height + self.spacing) * 2, self.button_width, self.button_height, "Begin", "BEGIN"),
            Button(self.margin_x, start_y + (self.button_height + self.spacing) * 3, self.button_width, self.button_height, "Exit", "EXIT")
        ]

    def draw(self):
        # don't draw the main menu while the level scroller is open
        if level_scroller.visible:
            return
        screen.blit(menu_background, (0, 0))
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event):
        for button in self.buttons:
            action = button.handle_event(event)
            if action:
                menu_button_accept.play()
                return action

# ----------------------------------------
# level scroller class
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
        self.score_font = pygame.font.Font(None, 26)
        self.scroll_speed = 18
        self.hovered_card = None

        # panel is slightly taller so best score text fits under the cards
        panel_width = WIDTH - 200
        panel_height = 280

        self.panel_rect = pygame.Rect(
            (WIDTH - panel_width) // 2,
            (HEIGHT - panel_height) // 2,
            panel_width,
            panel_height
        )

        self.button_width = 220
        self.button_height = 60

        # return button sits just below the panel
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
        # total pixel width of all cards laid out side by side
        return len(LEVEL_ORDER) * (self.card_width + self.card_spacing) - self.card_spacing

    def _max_scroll(self):
        # how far we can scroll before running out of cards
        visible_width = self.panel_rect.width - 40
        return max(0, self._total_content_width() - visible_width)

    def _is_unlocked(self, level_name):
        # level 1 is always available; the rest need the previous level completed
        idx = LEVEL_ORDER.index(level_name)
        if idx == 0:
            return True
        return LEVEL_ORDER[idx - 1] in completed_levels

    def draw(self, surface):
        if not self.visible:
            return

        pygame.draw.rect(surface, BLACK, self.panel_rect, border_radius=12)
        pygame.draw.rect(surface, ORANGE, self.panel_rect, 3, border_radius=12)

        title = self.title_font.render("Select Level", True, WHITE)
        surface.blit(title, (self.panel_rect.x + 20, self.panel_rect.y + 14))

        # clip the card area so scrolled cards don't bleed outside the panel
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
            # offset each card by the current scroll position
            card_x = (self.panel_rect.x + 20) + i * (self.card_width + self.card_spacing) - self.scroll_offset
            card_y = self.panel_rect.y + 58
            card_rect = pygame.Rect(card_x, card_y, self.card_width, self.card_height)

            unlocked = self._is_unlocked(level_name)
            done = level_name in completed_levels
            hovered = card_rect.collidepoint(mouse_pos) and unlocked and clip_rect.collidepoint(mouse_pos)

            if hovered:
                self.hovered_card = level_name

            # colour the card green if done, orange on hover, dark grey if locked
            if done:
                fill = (0, 120, 40) if not hovered else (0, 160, 55)
            elif unlocked:
                fill = (60, 60, 60) if not hovered else ORANGE
            else:
                fill = (30, 30, 30)

            pygame.draw.rect(surface, fill, card_rect, border_radius=10)
            border_colour = WHITE if done else (GREY if not hovered else ORANGE)
            pygame.draw.rect(surface, border_colour, card_rect, 2, border_radius=10)

            display = level_name.replace("LEVEL_", "Level ")
            label = self.label_font.render(display, True, WHITE if unlocked else GREY)
            label_rect = label.get_rect(center=(card_rect.centerx, card_rect.centery - 18))
            surface.blit(label, label_rect)

            # show Done / Play / Locked depending on state
            if done:
                tag = self.label_font.render("Done", True, (180, 255, 180))
            elif unlocked:
                tag = self.label_font.render("Play", True, (220, 220, 220))
            else:
                tag = self.label_font.render("Locked", True, (120, 120, 120))
            tag_rect = tag.get_rect(center=(card_rect.centerx, card_rect.centery + 8))
            surface.blit(tag, tag_rect)

            # show the player's best score at the bottom of the card if they have one
            if level_name in best_scores:
                score_text = self.score_font.render(f"Best: {best_scores[level_name]}", True, YELLOW)
                score_rect = score_text.get_rect(center=(card_rect.centerx, card_rect.bottom - 12))
                surface.blit(score_text, score_rect)

        # restore the old clip before drawing anything outside the panel
        surface.set_clip(old_clip)
        self.return_button.draw(surface)

        # draw scroll arrows only when there's content to scroll towards
        if self.scroll_offset > 0:
            pygame.draw.polygon(surface, WHITE, [
                (self.panel_rect.x + 8,  self.panel_rect.centery + 20),
                (self.panel_rect.x + 22, self.panel_rect.centery + 8),
                (self.panel_rect.x + 22, self.panel_rect.centery + 32)
            ])
        if self.scroll_offset < self._max_scroll():
            rx = self.panel_rect.right
            pygame.draw.polygon(surface, WHITE, [
                (rx - 8,  self.panel_rect.centery + 20),
                (rx - 22, self.panel_rect.centery + 8),
                (rx - 22, self.panel_rect.centery + 32)
            ])

    def handle_event(self, event):
        if not self.visible:
            return None

        # arrow keys scroll the cards
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed * 3)
            if event.key == pygame.K_RIGHT:
                self.scroll_offset = min(self._max_scroll(), self.scroll_offset + self.scroll_speed * 3)

        # mouse wheel also scrolls
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed)
            if event.button == 5:
                self.scroll_offset = min(self._max_scroll(), self.scroll_offset + self.scroll_speed)

            action = self.return_button.handle_event(event)
            if action:
                menu_button_accept.play()
                return action

            # clicking a hovered unlocked card starts that level
            if event.button == 1 and self.hovered_card:
                menu_button_accept.play()
                return self.hovered_card

        return None

# ----------------------------------------
# particle system
# ----------------------------------------
class Particle:
    # a single thrust or explosion particle
    def __init__(self, x, y, vx, vy, lifetime, colour, size=3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime       # total frames this particle lives
        self.age = 0
        self.colour = colour
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.06   # slight gravity so particles arc downward
        self.age += 1

    @property
    def alive(self):
        # particle dies once it hits its age limit
        return self.age < self.lifetime

    def draw(self, surface):
        # fade out and shrink the particle as it gets older
        alpha_ratio = 1.0 - (self.age / self.lifetime)
        radius = max(1, int(self.size * alpha_ratio))
        r = int(self.colour[0] * alpha_ratio)
        g = int(self.colour[1] * alpha_ratio)
        b = int(self.colour[2] * alpha_ratio)
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), radius)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_thrust(self, lander_x, lander_y, angle):
        rad = math.radians(angle)
        # work out where the engine nozzle is in world space
        nozzle_x = lander_x + math.sin(rad) * 22
        nozzle_y = lander_y + math.cos(rad) * 20

        for _ in range(3):
            spread = random.uniform(-0.5, 0.5)
            speed  = random.uniform(1.5, 3.5)
            vx = math.sin(rad) * speed + spread
            vy = math.cos(rad) * speed + spread
            lifetime = random.randint(10, 20)
            # mix orange and yellow shades for a realistic flame look
            colour = random.choice([
                (255, 140,  0),
                (255, 200, 50),
                (255,  80,  0),
                (255, 255, 150)
            ])
            self.particles.append(Particle(nozzle_x, nozzle_y, vx, vy, lifetime, colour, size=random.randint(2, 5)))

    def emit_explosion(self, x, y):
        # burst of debris in all directions when the lander crashes
        for _ in range(60):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.0, 6.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 3)  # bias upward so it looks like an explosion
            lifetime = random.randint(20, 45)
            colour = random.choice([
                (255, 80,   0),
                (255, 200, 50),
                (200, 200, 200),
                (255, 255,  0),
                (150, 150, 150)
            ])
            self.particles.append(Particle(x, y, vx, vy, lifetime, colour, size=random.randint(2, 6)))

    def update(self):
        # remove dead particles and update the rest
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# ----------------------------------------
# screen shake
# ----------------------------------------
class ScreenShake:
    def __init__(self):
        self.frames_remaining = 0
        self.magnitude = SHAKE_MAGNITUDE

    def trigger(self):
        # start a fresh shake — called on crash
        self.frames_remaining = SHAKE_DURATION

    def get_offset(self):
        # return (0, 0) once the shake has finished
        if self.frames_remaining <= 0:
            return (0, 0)
        # taper the magnitude so the shake smoothly dies down
        ratio = self.frames_remaining / SHAKE_DURATION
        mag = int(self.magnitude * ratio)
        ox = random.randint(-mag, mag)
        oy = random.randint(-mag, mag)
        return (ox, oy)

    def update(self):
        if self.frames_remaining > 0:
            self.frames_remaining -= 1

# ----------------------------------------
# wind system
# ----------------------------------------
class Wind:
    # applies a horizontal force to the lander on levels 4 and 5
    def __init__(self, level_name):
        self.active = level_name in WIND_LEVELS
        self.level_name = level_name

        if level_name == "LEVEL_4":
            self.base_force = WIND_FORCE_LEVEL_4
        elif level_name == "LEVEL_5":
            self.base_force = WIND_FORCE_LEVEL_5
        else:
            self.base_force = 0.0

        # pick a random starting wind direction; positive = right, negative = left
        self.direction = random.choice([-1, 1])
        # gust timer is only used on level 5 to add unpredictable changes
        self.gust_timer = 0
        self.current_force = self.base_force * self.direction

    def update(self):
        if not self.active:
            return
        # on level 5 the wind randomly shifts direction every ~3 seconds
        if self.level_name == "LEVEL_5":
            self.gust_timer += 1
            if self.gust_timer >= 180:   # roughly every 3 seconds at 60fps
                self.gust_timer = 0
                gust_delta = random.uniform(-0.01, 0.01)
                # clamp so the wind doesn't go completely wild
                self.current_force = max(-WIND_FORCE_LEVEL_5 * 1.5,
                                         min(WIND_FORCE_LEVEL_5 * 1.5,
                                             self.current_force + gust_delta))

    def apply(self, lander):
        # push the lander sideways every frame while wind is active
        if self.active:
            lander.speed_x += self.current_force

    def draw_indicator(self, surface):
        # draw a small wind arrow and label on the HUD so the player knows which way the wind blows
        if not self.active:
            return

        arrow_x = WIDTH - 160
        arrow_y = 30
        strength = abs(self.current_force)
        direction = 1 if self.current_force >= 0 else -1

        # make the arrow longer when the wind is stronger
        shaft_len = int(strength / WIND_FORCE_LEVEL_5 * 80) + 30
        tip_x = arrow_x + direction * shaft_len
        pygame.draw.line(surface, CYAN, (arrow_x, arrow_y), (tip_x, arrow_y), 3)

        # arrowhead triangle pointing in the wind direction
        pygame.draw.polygon(surface, CYAN, [
            (tip_x, arrow_y),
            (tip_x - direction * 10, arrow_y - 7),
            (tip_x - direction * 10, arrow_y + 7)
        ])

        label = small_font.render("Wind", True, CYAN)
        surface.blit(label, (arrow_x - 50, arrow_y - 10))

# ----------------------------------------
# lander class
# ----------------------------------------
class Lander:
    def __init__(self):
        # start near the top-centre of the screen
        self.x = WIDTH // 2
        self.y = 120
        self.angle = 0
        self.speed_y = 0
        self.speed_x = 0

        self.thrust_sound_playing = False
        self.alive = True
        self.landed = False
        self.fuel = START_FUEL
        self.thrusting = False

        # load both images upfront so we can swap to the crash image instantly
        self.base_image     = self.scale_lander_image(pygame.image.load("Lander.png").convert_alpha())
        self.crash_image    = self.scale_lander_image(pygame.image.load("Lander_Explosion.png").convert_alpha())

        self.image = self.base_image
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def scale_lander_image(self, image):
        # shrink the raw image to the in-game lander size
        width  = int(image.get_width()  * LANDER_SCALE)
        height = int(image.get_height() * LANDER_SCALE)
        return pygame.transform.smoothscale(image, (width, height))

    def get_collision_rect(self):
        # shrink the hit-box a bit so the lander doesn't clip invisible pixels around the sprite
        collision_rect = self.rect.inflate(-self.rect.width * 0.45, -self.rect.height * 0.35)
        # shift it down slightly so the feet match the bottom of the sprite
        collision_rect.y += int(self.rect.height * 0.12)
        return collision_rect

    def update(self, gravity_scale=1.0, freeze_descent=False, landing_pad_rect=None,
               terrain_points=None, particle_system=None, screen_shake=None, wind=None):

        # stop thrust sound immediately when descent is frozen (tutorial freeze moments)
        if freeze_descent:
            if self.thrust_sound_playing:
                thrust_sound.stop()
                self.thrust_sound_playing = False

        self.thrusting = False
        keys = pygame.key.get_pressed()

        # gravity pulls the lander down every frame unless frozen
        if not freeze_descent:
            self.speed_y += GRAVITY * gravity_scale

        # apply wind push if this level has wind
        if wind and not freeze_descent:
            wind.apply(self)

        # SPACE fires the main thruster upward relative to the lander's angle
        if keys[pygame.K_SPACE] and self.fuel > 0 and not freeze_descent:
            rad = math.radians(self.angle)
            self.speed_x -= math.sin(rad) * THRUST
            self.speed_y -= math.cos(rad) * THRUST
            self.fuel -= 1
            self.thrusting = True

            # loop the thrust sound while the engine is firing
            if not self.thrust_sound_playing:
                thrust_sound.play(-1)
                self.thrust_sound_playing = True

            if particle_system:
                particle_system.emit_thrust(self.x, self.y, self.angle)
        else:
            # cut the engine sound as soon as the player releases SPACE
            if self.thrust_sound_playing:
                thrust_sound.stop()
                self.thrust_sound_playing = False

        # rotate the lander with the arrow keys
        if keys[pygame.K_LEFT]:
            self.angle += 1.5
        if keys[pygame.K_RIGHT]:
            self.angle -= 2.5

        # prevent the lander from flipping completely upside down
        self.angle = max(-90, min(90, self.angle))

        # rebuild the rotated sprite each frame to match the current angle
        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect  = self.image.get_rect(center=(self.x, self.y))

        # apply velocity; skip vertical movement when frozen
        if freeze_descent:
            self.speed_y = 0
        else:
            self.y += self.speed_y

        self.x += self.speed_x

        # --- landing and crash detection ---
        collision_rect = self.get_collision_rect()
        ground_top = get_terrain_y(terrain_points, collision_rect.centerx) if terrain_points else HEIGHT - 50

        over_landing_pad = False
        landing_surface_top = ground_top
        if landing_pad_rect is not None:
            over_landing_pad = landing_pad_rect.left <= collision_rect.centerx <= landing_pad_rect.right
            if over_landing_pad:
                # use whichever surface is higher — pad top or raw terrain
                landing_surface_top = min(ground_top, landing_pad_rect.top)

        if collision_rect.bottom >= landing_surface_top:
            # push the lander back up so it sits flush on the surface
            penetration = collision_rect.bottom - landing_surface_top
            self.y -= penetration
            self.rect = self.image.get_rect(center=(self.x, self.y))
            collision_rect = self.get_collision_rect()

            on_landing_pad = (
                landing_pad_rect is not None
                and over_landing_pad
                and abs(collision_rect.bottom - landing_pad_rect.top) <= 2
            )

            # safe landing: on the pad, slow enough, and nearly upright
            if on_landing_pad and abs(self.speed_y) <= SAFE_SPEED and abs(self.angle) <= 12:
                self.landed = True
            else:
                # anything else is a crash
                if self.alive:

                    self.alive = False

                    # swap to the explosion sprite
                    crash_rotated = pygame.transform.rotate(self.crash_image, self.angle)
                    self.image = crash_rotated
                    self.rect  = crash_rotated.get_rect(center=(self.x, self.y))
                    
                    explosion_sound.play()

                    # kick off particles and screen shake
                    if particle_system:
                        particle_system.emit_explosion(self.x, self.y)
                    if screen_shake:
                        screen_shake.trigger()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# ----------------------------------------
# ground class
# ----------------------------------------
class Ground:
    def __init__(self, level_name="LEVEL_1"):
        self.level_name = level_name
        level_data = LEVELS.get(level_name, LEVELS["LEVEL_1"])
        pad_data = level_data.get("landing_pad", LEVELS["LEVEL_1"]["landing_pad"])
        self.terrain_points = level_data.get("terrain_points", [(0, 700), (1200, 700)])

        # build the landing pad rectangle from the level data
        self.landing_pad_rect = pygame.Rect(
            pad_data["x"], pad_data["y"], pad_data["width"], pad_data["height"]
        )

    def draw(self, surface):
        # close the terrain polygon by adding two bottom-corner points
        poly_points = list(self.terrain_points)
        poly_points.append((self.terrain_points[-1][0], HEIGHT))
        poly_points.append((self.terrain_points[0][0],  HEIGHT))

        # use lighter colours for the tutorial so it looks distinct from the main levels
        if self.level_name == "TUTORIAL":
            ground_colour = (235, 235, 235)
            edge_colour   = (200, 200, 200)
        else:
            ground_colour = GROUND
            edge_colour   = (180, 60, 10)

        pygame.draw.polygon(surface, ground_colour, poly_points)
        pygame.draw.lines(surface, edge_colour, False, self.terrain_points, 3)
        # draw the landing pad on top of the terrain
        pygame.draw.rect(surface, WHITE, self.landing_pad_rect)

# ----------------------------------------
# HUD class
# ----------------------------------------
class HUD:
    def draw(self, lander, surface, wind=None):
        altitude = HEIGHT - 100 - lander.y

        texts = [
            f"Altitude: {int(altitude)}",
            f"Vertical Speed: {lander.speed_y:.1f}",
        ]

        for i, text in enumerate(texts):
            msg = font.render(text, True, WHITE)
            surface.blit(msg, (20, 20 + i * 50))

        self._draw_fuel_bar(lander, surface)

        if wind:
            wind.draw_indicator(surface)

    def _draw_fuel_bar(self, lander, surface):
        bar_x      = 20
        bar_y      = 130
        bar_width  = 200
        bar_height = 22

        # dark background track
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)

        fuel_ratio = lander.fuel / START_FUEL
        fill_width = int(bar_width * fuel_ratio)

        # colour the bar based on how much fuel is left
        if fuel_ratio > 0.5:
            bar_colour = GREEN
        elif fuel_ratio > 0.25:
            bar_colour = YELLOW
        else:
            bar_colour = RED

        if fill_width > 0:
            pygame.draw.rect(surface, bar_colour, (bar_x, bar_y, fill_width, bar_height), border_radius=4)

        # white border around the bar
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)

        label = small_font.render(f"Fuel: {lander.fuel}", True, WHITE)
        surface.blit(label, (bar_x + bar_width + 10, bar_y))

    def draw_level_name(self, level_name, surface):
        # convert "LEVEL_1" to "Level 1" for a friendlier display
        if level_name.startswith("LEVEL_"):
            display_name = level_name.replace("LEVEL_", "Level ")
        else:
            display_name = level_name.capitalize()

        msg = font.render(display_name, True, WHITE)
        rect = msg.get_rect(center=(WIDTH // 2, 20))
        surface.blit(msg, rect)

    def draw_timer(self, elapsed_seconds, surface):
        # format as MM:SS
        mins = int(elapsed_seconds) // 60
        secs = int(elapsed_seconds) % 60
        timer_text = small_font.render(f"Time: {mins:02d}:{secs:02d}", True, WHITE)
        surface.blit(timer_text, (20, 160))

# ----------------------------------------
# pause menu
# ----------------------------------------
class PauseMenu:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 72)
        self.sub_font   = pygame.font.Font(None, 38)

        # centre the panel on screen
        panel_w = 420
        panel_h = 340
        px = (WIDTH  - panel_w) // 2
        py = (HEIGHT - panel_h) // 2
        self.panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        btn_w = 280
        btn_h = 58
        cx = px + (panel_w - btn_w) // 2

        self.buttons = [
            Button(cx, py + 130, btn_w, btn_h, "Resume",       "RESUME"),
            Button(cx, py + 200, btn_w, btn_h, "Restart Level", "RESTART"),
            Button(cx, py + 270, btn_w, btn_h, "Main Menu",    "MENU"),
        ]

    def draw(self, surface):
        # semi-transparent black overlay to dim the game behind the pause panel
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (20, 20, 20),  self.panel_rect, border_radius=14)
        pygame.draw.rect(surface, ORANGE,         self.panel_rect, 3, border_radius=14)

        title = self.title_font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.y + 70))
        surface.blit(title, title_rect)

        # small hint reminding the player they can press P to resume quickly
        hint = self.sub_font.render("P  ·  resume", True, GREY)
        hint_rect = hint.get_rect(center=(self.panel_rect.centerx, self.panel_rect.y + 115))
        surface.blit(hint, hint_rect)

        for btn in self.buttons:
            btn.draw(surface)

    def handle_event(self, event):
        for btn in self.buttons:
            action = btn.handle_event(event)
            if action:
                menu_button_accept.play()
                return action
        return None

# ----------------------------------------
# tutorial guide class
# ----------------------------------------
class TutorialGuide:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 48)
        self.text_font  = pygame.font.Font(None, 34)
        self.tip_colour = (20, 20, 20)
        self.box_colour = (255, 255, 255)
        self.turn_intro_shown = False
        # how many frames to hold the lander in place while showing the turn tip
        self.turn_intro_frames = 75
        self.turn_intro_frames_remaining = self.turn_intro_frames
        self.current_step_index = None
        self.completed_steps = set()

    def get_steps(self, lander):
        # define each tutorial step and whether it's been accomplished yet
        return [
            {
                "title": "Use Main Thruster",
                "tip": "Hold SPACE to fire the main thruster.",
                "done": lander.fuel < START_FUEL   # any fuel use means the player fired
            },
            {
                "title": "Learn to Turn",
                "tip": "Use LEFT and RIGHT arrows to rotate the lander.",
                "done": abs(lander.angle) > 0
            }
        ]

    def get_step_states(self, lander):
        # merge live step state with anything previously marked complete
        steps = self.get_steps(lander)
        states = []
        for index, step in enumerate(steps):
            done = step["done"] or index in self.completed_steps
            states.append({"title": step["title"], "tip": step["tip"], "done": done})
        return states

    def update(self, lander):
        # nothing to guide if the lander is already done
        if not lander.alive or lander.landed:
            return {"freeze_descent": False, "gravity_scale": 0.5}

        steps = self.get_step_states(lander)

        # lock in any completed steps so they don't un-complete
        for index, step in enumerate(steps):
            if step["done"]:
                self.completed_steps.add(index)

        # find the first step that still needs doing
        next_step_index = len(steps)
        for index, step in enumerate(steps):
            if not step["done"]:
                next_step_index = index
                break

        self.current_step_index = next_step_index

        # freeze the lander briefly when the turning tip first appears so the player can read it
        turn_step_active = (self.current_step_index == 1
                            and 0 in self.completed_steps
                            and 1 not in self.completed_steps)
        if turn_step_active and not self.turn_intro_shown:
            self.turn_intro_frames_remaining -= 1
            freeze_descent = self.turn_intro_frames_remaining > 0
            if self.turn_intro_frames_remaining <= 0:
                self.turn_intro_shown = True
        else:
            freeze_descent = False

        # use half gravity in the tutorial so it's forgiving for new players
        return {"freeze_descent": freeze_descent, "gravity_scale": 0.5}

    def draw(self, lander, surface):
        # don't show the guide once the lander is done
        if not lander.alive or lander.landed:
            return

        steps = self.get_step_states(lander)
        active_step = None

        # pick the current active step
        if self.current_step_index is not None and self.current_step_index < len(steps):
            active_step = steps[self.current_step_index]
        else:
            for step in steps:
                if not step["done"]:
                    active_step = step
                    break

        # all steps done — prompt the player to land
        if active_step is None:
            active_step = {
                "title": "Tutorial Complete",
                "tip": "Great work! Finish the landing to continue.",
                "done": True
            }

        # draw the white tip box at the top of the screen
        panel = pygame.Rect(120, 20, WIDTH - 240, 90)
        pygame.draw.rect(surface, self.box_colour, panel, border_radius=12)
        pygame.draw.rect(surface, BLACK, panel, 3, border_radius=12)

        title_text = self.title_font.render(active_step["title"], True, self.tip_colour)
        tip_text   = self.text_font.render(active_step["tip"],   True, self.tip_colour)
        surface.blit(title_text, (panel.x + 20, panel.y + 12))
        surface.blit(tip_text,   (panel.x + 20, panel.y + 52))

# ----------------------------------------
# camera zoom functions
# ----------------------------------------
def get_zoom(lander, landing_pad_rect):
    # zoom in when the lander is close to the pad, zoom out when far away
    distance = math.hypot(lander.x - landing_pad_rect.centerx,
                          lander.y - landing_pad_rect.centery)
    return MAX_ZOOM if distance <= ZOOM_NEAR_DISTANCE else MIN_ZOOM

def draw_zoomed_scene(scene_surface, zoom, focus_x, focus_y, shake_offset=(0, 0)):
    # no scaling needed at 1x zoom; just blit with the shake offset applied
    if zoom <= 1.0:
        ox, oy = shake_offset
        screen.blit(scene_surface, (ox, oy))
        return

    # scale the whole scene up, then crop to the viewport centred on the focus point
    scaled_width  = int(WIDTH  * zoom)
    scaled_height = int(HEIGHT * zoom)
    scaled_scene  = pygame.transform.smoothscale(scene_surface, (scaled_width, scaled_height))

    scaled_focus_x = focus_x * zoom
    scaled_focus_y = focus_y * zoom

    # clamp so we never scroll outside the scaled image
    left = int(max(0, min(scaled_width  - WIDTH,  scaled_focus_x - WIDTH  / 2)))
    top  = int(max(0, min(scaled_height - HEIGHT, scaled_focus_y - HEIGHT / 2)))

    ox, oy = shake_offset
    screen.blit(scaled_scene, (ox, oy), area=pygame.Rect(left, top, WIDTH, HEIGHT))

# ----------------------------------------
# end-screen score display
# ----------------------------------------
def draw_end_screen(surface, lander, level_name, score, elapsed_time):

    if lander.landed:
        result_text = font.render("SAFE LANDING!", True, GREEN)
    else:
        result_text = font.render("CRASHED!", True, RED)

    result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 130))
    surface.blit(result_text, result_rect)

    # show the score breakdown panel only for non-tutorial successful landings
    if lander.landed and level_name != "TUTORIAL":

        panel = pygame.Rect(WIDTH // 2 - 240, HEIGHT // 2 - 80, 480, 190)

        pygame.draw.rect(surface, (0, 0, 0), panel, border_radius=10)
        pygame.draw.rect(surface, ORANGE, panel, 3, border_radius=10)

        fuel_score    = int((lander.fuel / START_FUEL) * 500)
        time_score    = max(0, int(300 - elapsed_time * 2))
        landing_bonus = 200

        lines = [
            f"Fuel bonus:    {fuel_score}",
            f"Time bonus:    {time_score}",
            f"Landing bonus: {landing_bonus}",
            f"TOTAL SCORE:   {score}",
        ]

        colours = [WHITE, WHITE, WHITE, YELLOW]

        for i, (line, col) in enumerate(zip(lines, colours)):
            txt = small_font.render(line, True, col)
            surface.blit(txt, (panel.x + 25, panel.y + 18 + i * 34))

        # show the personal best score if one exists
        if level_name in best_scores:
            best_txt = small_font.render(
                f"Best: {best_scores[level_name]}",
                True,
                CYAN
            )

            surface.blit(best_txt, (panel.x + 25, panel.bottom - 42))

    # context-sensitive prompt at the bottom
    if lander.landed:
        if level_name == "TUTORIAL":
            prompt = "Press SPACE for menu, R to retry"
        else:
            prompt = "Press SPACE for next level, R to retry, M for menu"
    else:
        prompt = "Press R to retry or M for menu"

    prompt_surf = small_font.render(prompt, True, WHITE)
    prompt_rect = prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
    surface.blit(prompt_surf, prompt_rect)

# ----------------------------------------
# game objects
# ----------------------------------------
def start_level(level_name):
    # reset every game object and start the chosen level fresh
    global lander, ground, background_image, game_state
    global current_level, tutorial_guide, current_level_index
    global particle_system, screen_shake, wind
    global level_start_ticks, level_elapsed_time, round_score

    current_level = level_name

    # keep current_level_index in sync with whichever level we're starting
    if level_name in LEVEL_ORDER:
        current_level_index = LEVEL_ORDER.index(level_name)

    lander           = Lander()
    ground           = Ground(level_name)
    background_image = load_level_background(level_name)
    particle_system  = ParticleSystem()
    screen_shake     = ScreenShake()
    wind             = Wind(level_name)
    # only create a tutorial guide for the tutorial level
    tutorial_guide   = TutorialGuide() if level_name == "TUTORIAL" else None

    level_start_ticks  = pygame.time.get_ticks()
    level_elapsed_time = 0.0
    round_score        = 0

    game_state = PLAYING


def return_to_menu():
    global game_state, tutorial_guide, level_scroller

    # make sure the thrust loop doesn't carry over into the menu
    thrust_sound.stop()
    tutorial_guide = None
    level_scroller.visible = False
    level_scroller.scroll_offset = 0
    game_state = MENU


def go_to_next_level():
    global current_level_index, current_level, completed_levels

    # tutorial completion just sends the player back to the menu
    if current_level == "TUTORIAL":
        return_to_menu()
        return

    # mark the current level as done and save progress
    completed_levels.add(current_level)
    write_save(completed_levels, best_scores)

    # advance to the next level, or return to menu if we've finished them all
    if current_level_index < len(LEVEL_ORDER) - 1:
        current_level_index += 1
        next_level = LEVEL_ORDER[current_level_index]
        start_level(next_level)
    else:
        return_to_menu()


# ----------------------------------------
# initialise globals
# ----------------------------------------
lander             = None
current_level      = "LEVEL_1"
ground             = Ground(current_level)
hud                = HUD()
menu               = Menu()
level_scroller     = LevelScroller()
pause_menu         = PauseMenu()
tutorial_guide     = None
particle_system    = ParticleSystem()
screen_shake       = ScreenShake()
wind               = Wind(current_level)
level_start_ticks  = 0
level_elapsed_time = 0.0
round_score        = 0

game_state = MENU

# ----------------------------------------
# main game loop
# ----------------------------------------
running = True
while running:

    # ---- event handling ----
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # M returns to menu from anywhere
            if event.key == pygame.K_m:
                return_to_menu()
                continue

            # Q quits the whole game
            if event.key == pygame.K_q:
                running = False

            # R restarts the current level at any point
            if event.key == pygame.K_r:
                start_level(current_level)

            # P toggles the pause state
            if event.key == pygame.K_p:
                if game_state == PLAYING:
                    game_state = PAUSED
                    thrust_sound.stop()
                    if lander:
                        lander.thrust_sound_playing = False
                elif game_state == PAUSED:
                    game_state = PLAYING

            # SPACE on the end screen advances to the next level
            if game_state == ENDED:
                if event.key == pygame.K_SPACE:
                    if current_level == "TUTORIAL":
                        return_to_menu()
                    else:
                        if lander and lander.landed:
                            go_to_next_level()

        # handle pause menu button clicks
        if game_state == PAUSED:
            action = pause_menu.handle_event(event)
            if action == "RESUME":
                game_state = PLAYING
            elif action == "RESTART":
                start_level(current_level)
            elif action == "MENU":
                return_to_menu()

        # handle main menu and level scroller interactions
        if game_state == MENU:
            result = None
            scroller_result = None

            if level_scroller.visible:
                scroller_result = level_scroller.handle_event(event)
            else:
                result = menu.handle_event(event)

            if scroller_result == "MENU_RETURN":
                return_to_menu()
            elif scroller_result in LEVEL_ORDER:
                # player picked a level from the scroller
                current_level_index = LEVEL_ORDER.index(scroller_result)
                start_level(scroller_result)

            if result == "BEGIN":
                # start from level 1
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

    # ---- update ----
    if game_state == PLAYING and lander is not None:

        # tick the in-level timer
        level_elapsed_time = (pygame.time.get_ticks() - level_start_ticks) / 1000.0

        wind.update()

        # let the tutorial guide control gravity and freeze flags
        tutorial_settings = {"freeze_descent": False, "gravity_scale": 1.0}
        if tutorial_guide is not None and current_level == "TUTORIAL":
            tutorial_settings = tutorial_guide.update(lander)

        lander.update(
            gravity_scale    = tutorial_settings["gravity_scale"],
            freeze_descent   = tutorial_settings["freeze_descent"],
            landing_pad_rect = ground.landing_pad_rect,
            terrain_points   = ground.terrain_points,
            particle_system  = particle_system,
            screen_shake     = screen_shake,
            wind             = wind
        )

        particle_system.update()
        screen_shake.update()

        # transition to the end screen once the lander has landed or crashed
        if lander.landed or not lander.alive:
            game_state = ENDED

            if current_level == "TUTORIAL":
                current_level_index = 0
            else:
                # calculate the score and update the best score if it's a new record
                round_score = calculate_score(lander.fuel, level_elapsed_time, lander.landed)
                if lander.landed:
                    prev_best = best_scores.get(current_level, 0)
                    if round_score > prev_best:
                        best_scores[current_level] = round_score
                    completed_levels.add(current_level)
                    write_save(completed_levels, best_scores)

    if game_state == PAUSED and lander is not None:
        # keep particles and shake going while paused so an explosion doesn't freeze mid-air
        particle_system.update()
        screen_shake.update()

    # ---- draw ----
    if game_state == MENU:
        if level_scroller.visible:
            level_scroller.draw(screen)
        else:
            menu.draw()

    else:
        # render the full game scene to an off-screen surface first so we can zoom/shake it
        scene_surface = pygame.Surface((WIDTH, HEIGHT))
        scene_surface.blit(background_image, (0, 0))
        ground.draw(scene_surface)
        particle_system.draw(scene_surface)
        if lander:
            lander.draw(scene_surface)

        # keep the camera midway between the lander and the landing pad
        camera_zoom    = get_zoom(lander, ground.landing_pad_rect) if lander else MIN_ZOOM
        camera_focus_x = (lander.x + ground.landing_pad_rect.centerx) / 2 if lander else WIDTH / 2
        camera_focus_y = (lander.y + ground.landing_pad_rect.centery) / 2 if lander else HEIGHT / 2

        shake_offset = screen_shake.get_offset()
        draw_zoomed_scene(scene_surface, camera_zoom, camera_focus_x, camera_focus_y, shake_offset)

        # hide the HUD when zoomed in so it doesn't obscure the landing
        hud_hidden_for_zoom = camera_zoom > MIN_ZOOM

        if not hud_hidden_for_zoom:
            if current_level != "TUTORIAL":
                hud.draw_level_name(current_level, screen)
            if current_level != "TUTORIAL" and lander:
                hud.draw(lander, screen, wind=wind)
                if game_state == PLAYING:
                    hud.draw_timer(level_elapsed_time, screen)

        # tutorial guide overlay sits on top of the HUD layer
        if tutorial_guide is not None and current_level == "TUTORIAL" and lander and not hud_hidden_for_zoom:
            tutorial_guide.draw(lander, screen)

        # end screen drawn on top of the game world
        if game_state == ENDED and lander:
            thrust_sound.stop()
            draw_end_screen(screen, lander, current_level, round_score, level_elapsed_time)

        # pause overlay is the very last thing drawn so it's always on top
        if game_state == PAUSED:
            pause_menu.draw(screen)

    clock.tick(60)
    pygame.display.flip()

pygame.quit()
sys.exit()