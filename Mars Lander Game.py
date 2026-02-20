import pygame
import sys
import random
from math import sin, cos, radians

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
w = screen.get_width()
h = screen.get_height()
pygame.display.set_caption("Mars Lander")
clock = pygame.time.Clock()

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (200,200,200)
BLUE = (50,150,255)
SKY = (255,150,100)
GROUND_COLOR = (200,80,30)
GREEN = (0,255,0)
RED = (255,0,0)
LOCKED = (100,100,100)

GRAVITY = 0.04
THRUST = 0.20
ROTATE_SPEED = 1.0
SAFE_Y = 3
SAFE_X = 2
SAFE_ANGLE = 10
GROUND_Y = h - 80
BOOST_TIME = 30
BOOM_SPEED = 12
START_FUEL = 1000

class Button:
    def __init__(self, txt, x, y, ww, hh):
        self.txt = txt
        self.box = pygame.Rect(x, y, ww, hh)
        self.col = GRAY

    def draw(self):
        pygame.draw.rect(screen, self.col, self.box)
        f = pygame.font.SysFont(None, 50)
        t = f.render(self.txt, True, BLACK)
        screen.blit(t, t.get_rect(center=self.box.center))

    def mouse_on(self):
        return self.box.collidepoint(pygame.mouse.get_pos())

# buttons
start_b = Button("Start", w//2-150, h//3, 300, 60)
levels_b = Button("Level Select", w//2-150, h//3+80, 300, 60)
exit_b = Button("Exit", w//2-150, h//3+160, 300, 60)

class Lander:
    def __init__(self):
        self.x = w // 2
        self.y = h // 10
        self.vx = 0
        self.vy = 0
        self.ang = 0
        self.fire = False
        self.timer = 0
        self.which_boost = 0
        self.ok = True
        self.win = False
        self.boom = False
        self.onpad = False
        self.fuel = START_FUEL

        self.norm = pygame.image.load('lander.png').convert_alpha()
        self.boosts = []
        self.boosts.append(pygame.image.load('lander_(boosterv1).png').convert_alpha())
        self.boosts.append(pygame.image.load('lander_(boosterv2).png').convert_alpha())
        self.boosts.append(pygame.image.load('lander_(boosterv3).png').convert_alpha())
        self.leftb = pygame.image.load('lander_(boosterL).png').convert_alpha()
        self.rightb = pygame.image.load('lander_(boosterR).png').convert_alpha()

        self.booms = []
        self.booms.append(pygame.image.load('Explosion1.png').convert_alpha())
        self.booms.append(pygame.image.load('Explosion2.png').convert_alpha())
        self.booms.append(pygame.image.load('Explosion3.png').convert_alpha())
        self.booms.append(pygame.image.load('Explosion4.png').convert_alpha())

        self.halfw = self.norm.get_width() // 2
        self.halfh = self.norm.get_height() // 2

        self.bf = 0
        self.bt = 0
        self.booming = False
        self.boomend = False

    def go(self, g, terr=None, k=None):
        if not self.ok:
            if self.boom and self.booming:
                self.bt = self.bt + 1
                if self.bt >= BOOM_SPEED:
                    self.bt = 0
                    self.bf = self.bf + 1
                    if self.bf >= 4:
                        self.booming = False
                        self.boomend = True
            return

        self.vy = self.vy + GRAVITY

        self.fire = k[pygame.K_SPACE]
        left = k[pygame.K_LEFT]
        right = k[pygame.K_RIGHT]

        if left:
            self.ang = self.ang - ROTATE_SPEED
        if right:
            self.ang = self.ang + ROTATE_SPEED

        if self.fire and self.fuel > 0:
            r = radians(self.ang)
            self.vx = self.vx + THRUST * sin(r)
            self.vy = self.vy - THRUST * cos(r)
            self.fuel = self.fuel - 1   # lose fuel when thrusting

            if self.timer <= 0:
                self.which_boost = random.randint(0,2)
                self.timer = BOOST_TIME
            self.timer = self.timer - 1
        else:
            self.fire = False   # no thrust if no fuel

        self.x = self.x + self.vx
        self.y = self.y + self.vy

        if self.x < self.halfw:
            self.x = self.halfw
            self.vx = 0
        if self.x > w - self.halfw:
            self.x = w - self.halfw
            self.vx = 0

        if terr != None:
            for i in range(len(terr)-1):
                x1,y1 = terr[i]
                x2,y2 = terr[i+1]
                if x1 <= self.x <= x2:
                    gy = y1 + (y2 - y1) * (self.x - x1) / (x2 - x1)
                    if self.y + self.halfh >= gy:
                        self.y = gy - self.halfh
                        self.onpad = g.pad_x <= self.x <= g.pad_x + g.pad_w
                        if self.onpad and self.vy < SAFE_Y and abs(self.vx) < SAFE_X and abs(self.ang) < SAFE_ANGLE:
                            self.win = True
                        else:
                            self.boom = True
                            self.booming = True
                            self.bf = 0
                            self.bt = 0
                            self.boomend = False
                        self.ok = False
                        self.vx = 0
                        self.vy = 0
                        return
        else:
            if self.y + self.halfh >= GROUND_Y:
                self.y = GROUND_Y - self.halfh
                self.onpad = g.pad_x <= self.x <= g.pad_x + g.pad_w
                if self.onpad and self.vy < SAFE_Y and abs(self.vx) < SAFE_X and abs(self.ang) < SAFE_ANGLE:
                    self.win = True
                else:
                    self.boom = True
                    self.booming = True
                    self.bf = 0
                    self.bt = 0
                    self.boomend = False
                self.ok = False
                self.vx = 0
                self.vy = 0

    def getpic(self, k):
        if self.booming or self.boomend:
            n = min(self.bf, 3)
            return self.booms[n]
        if self.fire:
            return self.boosts[self.which_boost]
        if k[pygame.K_LEFT]:
            return self.leftb
        if k[pygame.K_RIGHT]:
            return self.rightb
        return self.norm

    def drawpic(self, k):
        p = self.getpic(k)
        r = pygame.transform.rotate(p, -self.ang)
        rr = r.get_rect(center=(self.x, self.y))
        screen.blit(r, rr)

    def draw_fuel(self):
        f = pygame.font.SysFont(None, 40)
        txt = f.render("Fuel: " + str(self.fuel), True, WHITE)
        screen.blit(txt, (20, 20))

class FlatG:
    def __init__(self):
        self.pad_w = 120
        self.pad_h = 20
        self.pad_x = random.randint(100, w - self.pad_w - 100)
        self.pad_y = GROUND_Y - 10
        self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_w, self.pad_h)

    def draw(self):
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, w, h - GROUND_Y))
        pygame.draw.rect(screen, (150,150,150), self.pad_rect)

class HillG:
    def __init__(self):
        self.pad_w = 120
        self.pad_h = 20
        self.pts = []
        x = 0
        y = GROUND_Y + random.randint(-40,40)
        while x < w:
            self.pts.append((x, y))
            x = x + random.randint(80,150)
            y = y + random.randint(-60,60)
            if y < h//2: y = h//2
            if y > h-100: y = h-100
        self.pts.append((w, self.pts[-1][1]))

        # make a flat spot for the pad
        spot = random.randint(3, len(self.pts)-5)
        flat_y = (self.pts[spot][1] + self.pts[spot+1][1]) // 2
        self.pts[spot] = (self.pts[spot][0], flat_y)
        self.pts[spot+1] = (self.pts[spot+1][0], flat_y)

        mid = (self.pts[spot][0] + self.pts[spot+1][0]) // 2
        self.pad_x = mid - self.pad_w // 2
        self.pad_y = flat_y - self.pad_h
        self.pad_rect = pygame.Rect(self.pad_x, self.pad_y, self.pad_w, self.pad_h)

    def draw(self):
        pts = self.pts + [(w,h),(0,h)]
        pygame.draw.polygon(screen, GROUND_COLOR, pts)
        pygame.draw.rect(screen, (150,150,150), self.pad_rect)

def msg(txt, c):
    bigf = pygame.font.SysFont(None, int(h/7.5))
    m = bigf.render(txt, True, c)
    screen.blit(m, (w//2 - m.get_width()//2, h//2 - 50))

    smf = pygame.font.SysFont(None, int(h/15))
    qm = smf.render("Press Q or ESC to quit", True, WHITE)
    screen.blit(qm, (w//2 - qm.get_width()//2, h//2 + 50))

def play1(unl):
    g = FlatG()
    s = Lander()

    play = True
    won = False
    while play:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q or ev.key == pygame.K_ESCAPE:
                    play = False
                if won and ev.key == pygame.K_SPACE:
                    play = False

        kk = pygame.key.get_pressed()
        s.go(g, None, kk)
        screen.fill(SKY)
        g.draw()
        s.drawpic(kk)
        s.draw_fuel()

        if not s.ok:
            if s.win:
                msg("Good Landing! Press SPACE for Level 2", GREEN)
                unl[0] = True
                won = True
            else:
                msg("Crash!", RED)
                pygame.display.flip()
                pygame.time.wait(3000)
                play = False

        pygame.display.flip()
        clock.tick(60)

    return unl

def play2():
    g = HillG()
    s = Lander()

    play = True
    while play:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q or ev.key == pygame.K_ESCAPE:
                    play = False

        kk = pygame.key.get_pressed()
        s.go(g, g.pts, kk)
        screen.fill(SKY)
        g.draw()
        s.drawpic(kk)
        s.draw_fuel()

        if not s.ok:
            if s.win:
                msg("Good Landing! Level 2 Done", GREEN)
            else:
                msg("Crash!", RED)
            pygame.display.flip()
            pygame.time.wait(3000)
            play = False

        pygame.display.flip()
        clock.tick(60)

def levels(unl):
    b1 = Button("Level 1", w//2-150, h//3, 300, 60)
    b2 = Button("Level 2", w//2-150, h//3+80, 300, 60, BLUE if unl[0] else LOCKED)
    bk = Button("Back", w//2-150, h//3+160, 300, 60)

    r = True
    while r:
        screen.fill(WHITE)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if b1.mouse_on():
                    play1(unl)
                if b2.mouse_on() and unl[0]:
                    play2()
                if bk.mouse_on():
                    r = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    r = False

        b1.draw()
        b2.draw()
        bk.draw()

        pygame.display.flip()
        clock.tick(60)

def menu():
    unl = [False]

    r = True
    while r:
        screen.fill(WHITE)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if start_b.mouse_on():
                    unl = play1(unl)
                    if unl[0]:
                        screen.fill(SKY)  # back to sky, no white flash
                        msg("Level 1 Done! Press SPACE for Level 2", GREEN)
                        pygame.display.flip()
                        ww = True
                        while ww:
                            for eev in pygame.event.get():
                                if eev.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                                if eev.type == pygame.KEYDOWN:
                                    if eev.key == pygame.K_SPACE:
                                        play2()
                                        ww = False
                                    if eev.key == pygame.K_q or eev.key == pygame.K_ESCAPE:
                                        ww = False
                if levels_b.mouse_on():
                    levels(unl)
                if exit_b.mouse_on():
                    pygame.quit()
                    sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        start_b.color = BLUE if start_b.mouse_on() else GRAY
        levels_b.color = BLUE if levels_b.mouse_on() else GRAY
        exit_b.color = BLUE if exit_b.mouse_on() else GRAY

        start_b.draw()
        levels_b.draw()
        exit_b.draw()

        pygame.display.flip()
        clock.tick(60)

menu()