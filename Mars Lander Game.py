# -------------------------
# Imported Libraries
# -------------------------
import pygame # import the pygame library
import sys # import sys for exiting the program

# -------------------------
# Constants
# -------------------------
WIDTH = 800 # screen width in pixels
HEIGHT = 600 # screen height in pixels
GRAVITY = 0.1 # how fast the lander falls
THRUST = 0.25 # how strong the space key thrust is
START_FUEL = 500 # starting amount of fuel
SAFE_SPEED = 3 # maximum safe landing speed

# -------------------------
# Colours
# -------------------------
SKY = (255, 150, 100)
GROUND = (200, 80, 30)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# -------------------------
# Pygame Setup
# -------------------------
pygame.init() # start pygame
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # create game window
pygame.display.set_caption("Mars Lander") # window title
clock = pygame.time.Clock() # control frame rate
font = pygame.font.Font(None, 50) # font for on-screen text


# -------------------------
# Lander Class
# -------------------------
class Lander:
    def __init__(self):
        self.x = WIDTH // 2#start in middle of screen
        self.y = 100#start near the top
        self.angle = 0 # start upright
        self.speed = 0#vertical speed
        self.fuel = START_FUEL#current fuel
        self.alive = True#true until landed/crashed

        self.base_image = pygame.image.load("lander.png").convert_alpha() # Loads lander image
        self.booster_image = pygame.image.load("lander_(boosterv1).png").convert_alpha() # Loads booster image


        self.image = self.base_image # Current lander image variable
        self.rect = self.image.get_rect(center=(self.x, self.y)) # Centers lander image on rectangle for positioning
        
        self.image = pygame.image.load("lander.png").convert_alpha()#load your image
        self.rect = self.image.get_rect()#rectangle for positioning
        self.rect.centerx = self.x#centre the image horizonta$lly
        self.rect.centery = self.y#centre the image vertically

    def update(self):
        if not self.alive:#stop updating after landing
            return
            
        self.speed += GRAVITY#gravity pulls down every frame
        
        keys = pygame.key.get_pressed() # check which keys are pressed
        if keys[pygame.K_SPACE] and self.fuel > 0: # space key + fuel = thrust
            self.speed -= THRUST # push upwards
            self.fuel -= 1 # use 1 unit of fuel
            self.image = pygame.image.load("lander_(boosterv1).png").convert_alpha() # change image to show thrust

        key = pygame.key.get_pressed() # check keys again to reset image
        if not key[pygame.K_SPACE]: # if space is not pressed, show normal image
            self.image = pygame.image.load("lander.png").convert_alpha() # reset to normal image
            
        self.y += self.speed#move the lander
        self.rect.centery = self.y#update image position

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ARROW_LEFT]: # check for left key being pressed
            self.angle += 5 # rotate left
            
        if keys[pygame.K_ARROW_RIGHT]: # check for right key being pressed
            self.angle -= 5 # rotate right

        self.image = pygame.transform.rotate(self.base_image, self.angle)   # note: angle in degrees, positive = counter-clockwise
        self.rect = self.image.get_rect(center=self.rect.center)  # keep centered after rotate
            
        if self.y > HEIGHT - 100:#hit the ground
            self.y = HEIGHT - 100#lock to ground level
            self.rect.centery = self.y#update image
            self.alive = False#landing complete

    def draw(self):
        screen.blit(self.image, self.rect)#draw the spaceship image


# -------------------------
# Ground class
# -------------------------
class Ground:
    def draw(self):
        pygame.draw.rect(screen, GROUND, (0, HEIGHT-50, WIDTH, 50))#main ground
        pygame.draw.rect(screen, (150, 150, 150), (WIDTH//2-100, HEIGHT-55, 200, 10))#flat landing pad


# -------------------------
# HUD Class
# -------------------------
class HUD:
    def draw(self, lander):
        altitude = HEIGHT - 100 - lander.y#distance above ground
        
        texts = [#information to show
            f"Altitude: {int(altitude)}",
            f"Speed: {lander.speed:.1f}",
            f"Fuel: {int(lander.fuel)}"
        ]
        
        for i, text in enumerate(texts):#display each line
            msg = font.render(text, True, WHITE)
            screen.blit(msg, (20, 20 + i*50))
            
        if not lander.alive:#show result when landed
            if lander.speed < SAFE_SPEED:
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

# -------------------------
# Main Game Loop
# -------------------------
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