#!/usr/bin/env python3
"""
Luigi's Mansion: ONE SHOT (Vibes Edition)
-------------------------------------------------
Famicom-style beeps/boops, random full mansion, vibes mode, single file.
No assets. No mercy. 60fps, Mac safe.
Controls:
  Arrow keys ... Move
  SPACE ........ Flashlight stun (front only)
  ENTER ........ Vacuum stunned ghost (if touching)
  V ............ Toggle Vibes Mode (color/fog/rave)
  ESC .......... Quit
"""

import pygame, sys, random, math, time, numpy as np

# --- SYSTEM INIT
pygame.init()
pygame.mixer.init()
W, H = 960, 720
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("consolas", 36)
pygame.display.set_caption("Luigi's Mansion: ONE SHOT – Vibes Mode")
FPS = 60
BG = (24, 24, 36)

# --- BEEPS & BOOPS (Famicom, actual sound)
def beep(freq=660, dur=80, vol=0.22):
    fs = 44100
    t = np.linspace(0, dur/1000, int(fs * (dur/1000)), False)
    wave = (np.sin(freq * 2 * np.pi * t) * vol * 32767).astype(np.int16)
    snd = pygame.sndarray.make_sound(np.repeat(wave[:, None], 2, axis=1))
    snd.play()

def fami_beep(tone=0, dur=90):
    tones = [392, 524, 660, 784, 988, 1174, 1318, 1568]
    beep(freq=tones[tone%len(tones)], dur=dur, vol=0.26)

def fami_boopsuccess(): fami_beep(2, 120)
def fami_boopfail(): fami_beep(6, 220)
def fami_stun(): fami_beep(3, 40)
def fami_step(): fami_beep(random.randint(0, 3), 30)
def fami_stairs(): fami_beep(7, 250)

# --- VIBES MODE COLORS
VIBES = [(200,64,255), (64,255,192), (64,224,255), (255,224,64), (40,255,40)]
def get_vibe_color():
    t = time.time()*3
    i = int(t) % len(VIBES)
    j = (i+1)%len(VIBES)
    f = t-int(t)
    return tuple(int(VIBES[i][k]*(1-f)+VIBES[j][k]*f) for k in range(3))

# --- FLOOR/ROOM STRUCTURE ---
class Room:
    def __init__(s, i, x, y):
        s.i, s.x, s.y = i, x, y
        s.doors = []
        s.ghosts = []
        s.has_stairs = False
        s.visited = False

class Mansion:
    def __init__(s, n_floors=4):
        s.floors = []
        for fl in range(n_floors):
            n = random.randint(6,10)
            rooms = []
            for i in range(n):
                rx, ry = random.randint(1,8), random.randint(1,5)
                rooms.append(Room(i, rx, ry))
            # connect rooms linearly then randomly
            for i in range(n-1):
                rooms[i].doors.append(rooms[i+1])
                rooms[i+1].doors.append(rooms[i])
            for _ in range(n//2):
                a,b = random.sample(rooms,2)
                if b not in a.doors: a.doors.append(b); b.doors.append(a)
            # Add stairs to one room (except final floor)
            if fl < n_floors-1:
                rooms[random.randint(1, n-2)].has_stairs = True
            # Add ghosts to random rooms
            for r in rooms:
                if random.random()<.5: r.ghosts.append([r.x*96+48, r.y*96+48, 0])
            s.floors.append(rooms)
        s.cur_floor, s.cur_room = 0, 0
        s.luigi_room = s.floors[0][0]
        s.luigi_room.visited = True

    def goto_room(s, room):
        s.luigi_room = room
        room.visited = True
        fami_step()

    def up_stairs(s):
        if s.cur_floor < len(s.floors)-1:
            s.cur_floor += 1
            s.cur_room = 0
            s.luigi_room = s.floors[s.cur_floor][0]
            s.luigi_room.visited = True
            fami_stairs()
            return True
        return False

# --- PLAYER ---
class Luigi:
    def __init__(s):
        s.x, s.y = 144, 144
        s.facing = (1,0)
        s.flash_time = 0
        s.stun_ghost = None
        s.flash_cool = 0
        s.vacuum_cool = 0

    def move(s, dx, dy, mansion):
        s.x = max(32, min(W-32, s.x+dx*16))
        s.y = max(32, min(H-32, s.y+dy*16))
        if dx or dy:
            fami_step()
            if dx>0: s.facing=(1,0)
            elif dx<0: s.facing=(-1,0)
            elif dy>0: s.facing=(0,1)
            elif dy<0: s.facing=(0,-1)

    def flash(s, ghosts):
        if s.flash_cool > 0: return
        s.flash_cool = 40
        fami_stun()
        fx, fy = s.facing
        hit = None
        for g in ghosts:
            gx,gy,_ = g
            if abs(s.x+fx*50-gx)<60 and abs(s.y+fy*50-gy)<60:
                g[2]=30
                hit = g
        if hit: s.stun_ghost = hit

    def vacuum(s, ghosts):
        if s.vacuum_cool > 0 or not s.stun_ghost: return
        gx,gy,stun = s.stun_ghost
        if abs(s.x-gx)<64 and abs(s.y-gy)<64 and stun>0:
            ghosts.remove(s.stun_ghost)
            s.stun_ghost = None
            s.vacuum_cool = 35
            fami_boopsuccess()
        else:
            fami_boopfail()

# --- GHOSTS ---
def move_ghosts(room, luigi):
    for g in room.ghosts:
        gx,gy,stun = g
        if stun>0: g[2]-=1; continue
        angle = math.atan2(luigi.y-gy, luigi.x-gx)
        g[0] += math.cos(angle)*2
        g[1] += math.sin(angle)*2
        g[0] += random.uniform(-0.8,0.8)
        g[1] += random.uniform(-0.8,0.8)

def ghost_collision(room, luigi):
    for g in room.ghosts:
        gx,gy,stun = g
        if stun==0 and abs(luigi.x-gx)<40 and abs(luigi.y-gy)<40:
            fami_boopfail()
            return True
    return False

# --- DRAW ---
def draw_room(room, floor, vibes, luigi):
    bg = get_vibe_color() if vibes else BG
    screen.fill(bg)
    # Draw "fog"
    for i in range(12):
        color = get_vibe_color() + (80,) if vibes else (32,32,32,88)
        s = pygame.Surface((120,120), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (60,60), random.randint(40,90))
        screen.blit(s, (random.randint(0,W-120),random.randint(0,H-120)))
    # Draw rooms as rectangles
    for r in floor:
        col = (80,60,100) if not r.visited else (128,120,160)
        pygame.draw.rect(screen, col, (r.x*96, r.y*96, 88, 88), 3)
        if r.has_stairs: pygame.draw.rect(screen, (255,240,80), (r.x*96+36, r.y*96+36, 16,32))
    # Doors
    for dr in room.doors:
        pygame.draw.line(screen, (128,255,128), (room.x*96+44,room.y*96+44), (dr.x*96+44,dr.y*96+44), 8)
    # Ghosts
    for g in room.ghosts:
        gx,gy,stun = g
        clr = (240,255,240) if stun==0 else (255,64,128)
        pygame.draw.circle(screen, clr, (int(gx), int(gy)), 22)
        if stun>0:
            pygame.draw.circle(screen, (255,220,64), (int(gx), int(gy)), 10)
    # Luigi
    pygame.draw.circle(screen, (64,255,112), (int(luigi.x),int(luigi.y)), 24)
    # Flashlight beam
    if luigi.flash_cool>32:
        fx,fy = luigi.facing
        s = pygame.Surface((140,80), pygame.SRCALPHA)
        pygame.draw.polygon(s, (255,255,180,70),
            [(10,40),
             (130-fy*30, 10+fx*40),
             (130+fy*30, 70-fx*40)])
        screen.blit(s, (int(luigi.x), int(luigi.y)))
    # HUD
    msg = "FLOOR: %d  ROOMS: %d  GHOSTS: %d  [VIBES: %s]" % (mansion.cur_floor+1, len(floor), len(room.ghosts), "ON" if vibes else "OFF")
    txt = FONT.render(msg, 1, (255,255,255))
    screen.blit(txt, (24,8))

def draw_gameover():
    screen.fill((0,0,0))
    txt = FONT.render("ONE SHOT... GAME OVER!", 1, (255,40,64))
    screen.blit(txt, (W//2-260,H//2-40))
    pygame.display.flip()
    pygame.time.wait(2400)

# --- MAIN LOOP ---
mansion = Mansion(n_floors=random.randint(3,5))
luigi = Luigi()
vibes = False

while True:
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_ESCAPE: sys.exit()
            elif ev.key==pygame.K_v: vibes=not vibes
            elif ev.key in [pygame.K_LEFT, pygame.K_a]: luigi.move(-1,0,mansion)
            elif ev.key in [pygame.K_RIGHT, pygame.K_d]: luigi.move(1,0,mansion)
            elif ev.key in [pygame.K_UP, pygame.K_w]: luigi.move(0,-1,mansion)
            elif ev.key in [pygame.K_DOWN, pygame.K_s]: luigi.move(0,1,mansion)
            elif ev.key==pygame.K_SPACE: luigi.flash(mansion.luigi_room.ghosts)
            elif ev.key==pygame.K_RETURN: luigi.vacuum(mansion.luigi_room.ghosts)
            elif ev.key==pygame.K_TAB:
                # Move to random connected room
                if mansion.luigi_room.doors:
                    mansion.goto_room(random.choice(mansion.luigi_room.doors))

    # Move ghosts
    move_ghosts(mansion.luigi_room, luigi)

    # Check stairs
    if mansion.luigi_room.has_stairs and abs(luigi.x-(mansion.luigi_room.x*96+48))<44 and abs(luigi.y-(mansion.luigi_room.y*96+48))<44:
        if mansion.up_stairs():
            luigi.x, luigi.y = 144, 144
            fami_stairs()
            continue

    # Timers
    if luigi.flash_cool>0: luigi.flash_cool-=1
    if luigi.vacuum_cool>0: luigi.vacuum_cool-=1

    # Death
    if ghost_collision(mansion.luigi_room, luigi):
        draw_gameover()
        break

    # Draw everything
    draw_room(mansion.luigi_room, mansion.floors[mansion.cur_floor], vibes, luigi)
    pygame.display.flip()
    clock.tick(FPS)  # <-- THE ACTUAL WORKING LINE!

# No more haunted typo zone, just pure vibes.
