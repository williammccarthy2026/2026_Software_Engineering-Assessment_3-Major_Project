import pygame
import sys
import random
from math import sin, cos, radians

# start pygame
pygame.init()

# fixed window size (not fullscreen anymore)
WINDOW_W = 1000
WINDOW_H = 700
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Mars Lander")
clock = pygame.time.Clock()

# colours
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (200,200,200)
BLUE = (50,150,255)
SKY = (255,150,100)
GROUND_COLOR = (200,80,30)
GREEN = (0,255,0)
RED = (255,0,0)
LOCKED = (100,100,100)

# game values (use fractions of window size)
GRAVITY = 0.04
THRUST = 0.20
ROTATE_SPEED = 1.0
SAFE_Y = 3
SAFE_X = 2
SAFE_ANGLE = 10
GROUND_Y = WINDOW_H - 80
BOOST_TIME = 30
BOOM_SPEED = 12

class Button:
    def __init__(self, txt, x, y, ww, hh):
        self.txt = txt
        self.box = pygame.Rect(x, y, ww, hh)
        self.col = GRAY

    def draw(self):
        pygame.draw.rect(screen, self.col, self.box)
        f = pygame.font.SysFont(None, 40)
        t = f.render(self.txt, True, BLACK)
        screen.blit(t, t.get_rect(center=self.box.center))

    def mouse_on(self):
        return self.box.collidepoint(pygame.mouse.get_pos())

# menu buttons (centered in window)
start_b = Button("Start", WINDOW_W//2-150, WINDOW_H//3, 300, 60)
levels_b = Button("Level Select", WINDOW_W//2-150, WINDOW_H//3+80, 300, 60)
exit_b = Button("Exit", WINDOW_W//2-150, WINDOW_H//3+160, 300, 60)

class Lander:
    def __init__(self, fuel_start):
        self.x = WINDOW_W // 2
        self.y = WINDOW_H // 10
        self.vx = 0
        self.vy = 0
        self.ang = 0
        self.fire = False
        self.timer = 0
        self.boost_num = 0
        self.ok = True
        self.win = False
        self.boom = False
        self.onpad = False
        self.fuel = fuel_start

        self.norm = pygame.image.load('lander.png').convert_alpha()
        self.boosts = []
        for i in range(1,4):
            self.boosts.append(pygame.image.load(f'lander_(boosterv{i}).png').convert_alpha())
        self.leftb = pygame.image.load('lander_(boosterL).png').convert_alpha()
        self.rightb = pygame.image.load('lander_(boosterR).png').convert_alpha()

        self.booms = []
        for i in range(1,5):
            self.booms.append(pygame.image.load(f'Explosion{i}.png').convert_alpha())

        self.halfw = self.norm.get_width() // 2
        self.halfh = self.norm.get_height() // 2

        self.bf = 0
        self.bt = 0
        self.booming = False
        self.boomend = False

        # smoke
        self.smoke = []

    def go(self, g, terr=None, k=None):
        if not self.ok:
            if self.boom and self.booming:
                self.bt += 1
                if self.bt >= BOOM_SPEED:
                    self.bt = 0
                    self.bf += 1
                    if self.bf >= 4:
                        self.booming = False
                        self.boomend = True
            return

        self.vy += GRAVITY

        self.fire = k[pygame.K_SPACE]
        left = k[pygame.K_LEFT]
        right = k[pygame.K_RIGHT]

        if left:
            self.ang -= ROTATE_SPEED
        if right:
            self.ang += ROTATE_SPEED

        if self.fire and self.fuel > 0:
            r = radians(self.ang)
            self.vx += THRUST * sin(r)
            self.vy -= THRUST * cos(r)
            self.fuel -= 1
            if self.timer <= 0:
                self.boost_num = random.randint(0,2)
                self.timer = BOOST_TIME
            self.timer -= 1

            # smoke behind
            sx = self.x - 15 * sin(radians(self.ang))
            sy = self.y + 15 * cos(radians(self.ang))
            self.smoke.append([sx, sy, 30])

        else:
            self.fire = False

        self.x += self.vx
        self.y += self.vy

        if self.x < self.halfw:
            self.x = self.halfw
            self.vx = 0
        if self.x > w - self.halfw:
            self.x = w - self.halfw
            self.vx = 0

        # smoke fade
        for p in self.smoke[:]:
            p[2] -= 1
            if p[2] <= 0:
                self.smoke.remove(p)

        if terr is not None:
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
            return self.boosts[self.boost_num]
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

        # draw smoke
        for p in self.smoke:
            a = int(255 * (p[2] / 30))
            col = (200, 200, 200, a)
            pygame.draw.circle(screen, col, (int(p[0]), int(p[1])), 4)

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
    def __init__(self, lvl):
        self.pad_w = 120 - lvl * 10
        self.pad_h = 20
        self.pts = []
        x = 0
        y = GROUND_Y + random.randint(-40,40)
        while x < w:
            self.pts.append((x, y))
            x += random.randint(60,140)
            y += random.randint(-80,80)
            if y < h//2: y = h//2
            if y > h-100: y = h-100
        self.pts.append((w, self.pts[-1][1]))

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

def play_level(lvl, unl):
    if lvl == 1:
        g = FlatG()
        fuel = 1000
    else:
        g = HillG(lvl)
        fuel = 1000 - (lvl-1)*200

    s = Lander(fuel)

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
        s.go(g, g.pts if lvl > 1 else None, kk)
        screen.fill(SKY)
        g.draw()
        s.drawpic(kk)
        s.draw_fuel()

        if not s.ok:
            if s.win:
                txt = "Good! Press SPACE for Level " + str(lvl+1)
                msg(txt, GREEN)
                if lvl < 5:
                    unl[lvl] = True
                won = True
            else:
                msg("Crash!", RED)
                pygame.display.flip()
                pygame.time.wait(3000)
                play = False

        pygame.display.flip()
        clock.tick(60)

    return unl

def levels_screen(unl):
    bs = []
    for i in range(5):
        txt = "Level " + str(i+1)
        col = BLUE if (i == 0 or unl[i]) else LOCKED
        b = Button(txt, w//2-150, h//3 + i*70, 300, 60, col)
        bs.append(b)

    bk = Button("Back", w//2-150, h//3 + 350, 300, 60)

    r = True
    while r:
        screen.fill(WHITE)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i in range(5):
                    if bs[i].mouse_on() and (i == 0 or unl[i]):
                        unl = play_level(i+1, unl)
                if bk.mouse_on():
                    r = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    r = False

        for b in bs:
            b.draw()
        bk.draw()

        pygame.display.flip()
        clock.tick(60)

def menu():
    unl = [False] * 5

    r = True
    while r:
        screen.fill(WHITE)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if start_b.mouse_on():
                    unl = play_level(1, unl)
                if levels_b.mouse_on():
                    levels_screen(unl)
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