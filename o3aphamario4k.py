#!/usr/bin/env python3
"""
Mario Forever – zero‑shot vertical slice
---------------------------------------
5 worlds × 3 levels, castle + BoomBoom boss at the end of each world,
geared for 60 FPS on an M1 Mac.  Built on plain Pygame 2.x.

Author: (c) 2025 CatSama • Licence: MIT
"""
import sys, math, random, pathlib, pygame as pg
WIDTH, HEIGHT = 512, 448   # 16×14 tiles @32 px – NES aspect
FPS            = 60
GRAVITY        = 0.35
TILE           = 32
VIBES          = True   # global “vibe mode” toggle
BOOM_HP        = 3

# ---------------------------------------------------------------------------
# World / level catalogue ----------------------------------------------------
WORLDS = [
    {"name": "Grasslands",  "bg": (92,213, 99), "palette": (0,168, 40)},
    {"name": "Desert",      "bg": (231,198, 86), "palette": (219,142, 55)},
    {"name": "Snowfield",   "bg": (186,220,254), "palette": (126,188,252)},
    {"name": "Seaside",     "bg": (112,186,209), "palette": ( 82,146,179)},
    {"name": "Sky Realm",   "bg": (159,203,254), "palette": ( 90,167,254)},
]
LEVELS_PER_WORLD = 3

# ---------------------------------------------------------------------------
# Generic helpers ------------------------------------------------------------
def load_img(path, scale=1):  # placeholder – use solid surfaces for proto
    surf = pg.Surface((TILE, TILE))
    surf.fill((200,200,200))
    return pg.transform.scale(surf, (TILE*scale, TILE*scale))

def sign(x): return (x>0) - (x<0)

# ---------------------------------------------------------------------------
# Actor base class -----------------------------------------------------------
class Actor(pg.sprite.Sprite):
    def __init__(self, x, y, w=TILE, h=TILE):
        super().__init__()
        self.image  = pg.Surface((w,h), pg.SRCALPHA)
        self.rect   = self.image.get_rect(topleft=(x,y))
        self.vx     = self.vy = 0

    def update(self, tiles):
        # Horizontal
        self.rect.x += self.vx
        for t in self.rect.collidelistall(tiles):
            if self.vx>0: self.rect.right  = tiles[t].left
            if self.vx<0: self.rect.left   = tiles[t].right
        # Vertical
        self.vy += GRAVITY
        self.rect.y += self.vy
        on_ground = False
        for t in self.rect.collidelistall(tiles):
            if self.vy>0:
                self.rect.bottom = tiles[t].top
                self.vy = 0
                on_ground = True
            elif self.vy<0:
                self.rect.top = tiles[t].bottom
                self.vy = 0
        return on_ground

# ---------------------------------------------------------------------------
# Player ---------------------------------------------------------------------
class Player(Actor):
    SPEED  = 2.4
    JUMP   = -7.6
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((255,64,64))
        self.on_ground = False
    def update(self, tiles, keys):
        self.vx = (keys[pg.K_RIGHT] - keys[pg.K_LEFT]) * self.SPEED
        if keys[pg.K_z] and self.on_ground:
            self.vy = self.JUMP
        self.on_ground = super().update(tiles)

# ---------------------------------------------------------------------------
# BoomBoom boss --------------------------------------------------------------
class BoomBoom(Actor):
    SPEED = 1.8
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((255,128,0))
        self.hp      = BOOM_HP
        self.phase   = 0
    def update(self, tiles, player):
        # simple hop‑and‑charge pattern
        if self.phase==0:      # run toward player
            self.vx = self.SPEED * sign(player.rect.centerx - self.rect.centerx)
            grounded = super().update(tiles)
            if grounded and random.random()<0.015:
                self.vy = -8
        elif self.phase==1:    # defeated death‑spin
            self.vx = 0
            self.vy += GRAVITY
            self.rect.y += self.vy
        # collision with player
        if self.rect.colliderect(player.rect):
            if player.vy>0 and player.rect.bottom < self.rect.centery:
                self.hp -= 1
                player.vy = Player.JUMP/2
                if self.hp==0: self.phase=1
            else:
                # TODO: player damage routine
                pass

# ---------------------------------------------------------------------------
# Level object ---------------------------------------------------------------
class Level:
    def __init__(self, world_idx, idx):
        self.world_idx = world_idx
        self.idx       = idx
        self.is_castle = (idx == LEVELS_PER_WORLD-1)
        self.tiles     = self._make_tiles()
        player_start_x = TILE*2
        player_start_y = HEIGHT - TILE*3
        self.player    = Player(player_start_x, player_start_y)
        self.entities  = pg.sprite.Group(self.player)
        if self.is_castle:
            boss = BoomBoom(WIDTH-5*TILE, HEIGHT - 4*TILE)
            self.entities.add(boss)
            self.boss = boss
        self.scroll_x  = 0
    # -- tile generation -----------------------------------------------------
    def _make_tiles(self):
        tiles = []
        ground_y = HEIGHT - TILE*2
        for x in range(0, WIDTH*2, TILE):
            rect = pg.Rect(x, ground_y, TILE, TILE*2)
            tiles.append(rect)
        return tiles
    # -- update & draw -------------------------------------------------------
    def update(self, keys):
        self.player.update(self.tiles, keys)
        for e in self.entities:
            if isinstance(e, BoomBoom):
                e.update(self.tiles, self.player)
        # camera
        self.scroll_x = max(0, self.player.rect.centerx - WIDTH//3)
    def draw(self, surf):
        surf.fill(WORLDS[self.world_idx]["bg"])
        # vibes overlay
        if VIBES:
            t = pg.time.get_ticks()/1000
            wobble = math.sin(t*2)*4
            surf.scroll(int(wobble),0)
        # tiles
        for r in self.tiles:
            pg.draw.rect(surf, WORLDS[self.world_idx]["palette"],
                         r.move(-self.scroll_x,0))
        # entities
        for e in self.entities:
            surf.blit(e.image, (e.rect.x - self.scroll_x, e.rect.y))

# ---------------------------------------------------------------------------
# Game coordinator -----------------------------------------------------------
class Game:
    def __init__(self):
        pg.init()
        self.screen   = pg.display.set_mode((WIDTH,HEIGHT))
        pg.display.set_caption("Mario Forever • 5 Worlds demo")
        self.clock    = pg.time.Clock()
        self.world    = 0
        self.level_no = 0
        self.level    = Level(self.world, self.level_no)
    # -- level progression ---------------------------------------------------
    def next_level(self):
        self.level_no += 1
        if self.level_no >= LEVELS_PER_WORLD:
            self.level_no = 0
            self.world   += 1
            if self.world >= len(WORLDS):
                print("You beat the game!")
                pg.quit(); sys.exit(0)
        self.level = Level(self.world, self.level_no)
    # -- main loop -----------------------------------------------------------
    def run(self):
        while True:
            keys = pg.key.get_pressed()
            for ev in pg.event.get():
                if ev.type==pg.QUIT or (ev.type==pg.KEYDOWN and ev.key==pg.K_ESCAPE):
                    pg.quit(); sys.exit(0)
            self.level.update(keys)
            # win condition: reach far right or boss defeated
            if self.level.player.rect.right - self.level.scroll_x >= WIDTH-32:
                if not self.level.is_castle or self.level.boss.phase==1:
                    self.next_level()
            self.level.draw(self.screen)
            pg.display.flip()
            self.clock.tick(FPS)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    Game().run()
