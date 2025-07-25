import pygame as pg
import sys, random, math, array

# ----------------------- AUDIO CONFIG & SYNTH ------------------------
SAMPLE_RATE   = 44100          # Hz
pg.mixer.pre_init(SAMPLE_RATE, -16, 1)   # mono, 16‑bit signed
pg.init()

def synth_tone(freq=440.0, ms=100, volume=0.5):
    """Generate a pygame Sound containing a simple sine‑wave beep."""
    n_samples = int(SAMPLE_RATE * ms / 1000)
    buf = array.array("h")
    amplitude = int(volume * 32767)
    for s in range(n_samples):
        t = s / SAMPLE_RATE
        buf.append(int(amplitude * math.sin(2 * math.pi * freq * t)))
    return pg.mixer.Sound(buffer=buf.tobytes())

# Pre‑baked SFX
SFX_PADDLE = synth_tone(880,  60, 0.4)   # ‘beep’
SFX_BRICK  = synth_tone(440,  40, 0.5)   # ‘boop’
SFX_WALL   = synth_tone(330,  30, 0.4)
SFX_LOSE   = synth_tone(110, 400, 0.6)
SFX_WIN    = synth_tone(1320,300, 0.6)

# ---------------------------- GAME CONFIG ----------------------------
W, H          = 800, 600
FPS           = 60
BRICK_ROWS    = 6
BRICK_COLS    = 10
BRICK_GAP     = 4
PADDLE_W, PADDLE_H = 110, 15
BALL_R        = 8
BALL_SPEED    = 5.0
BG_COLOR      = (20, 20, 30)
PADDLE_COLOR  = (235, 235, 255)
BALL_COLOR    = (255, 215, 0)
BRICK_COLORS  = [(255, 77, 77), (255, 122, 66), (255, 205, 66),
                 (122, 255, 66), (66, 239, 255), (140, 122, 255)]
FONT_COLOR    = (250, 250, 250)

screen  = pg.display.set_mode((W, H))
clock   = pg.time.Clock()
font    = pg.font.SysFont("consolas", 24, bold=True)

# ------------------------- BUILD BRICK GRID --------------------------
BRICK_W = (W - BRICK_GAP * (BRICK_COLS + 1)) // BRICK_COLS
BRICK_H = 25
bricks  = []
top_offset = 60
for row in range(BRICK_ROWS):
    for col in range(BRICK_COLS):
        x = BRICK_GAP + col * (BRICK_W + BRICK_GAP)
        y = top_offset + row * (BRICK_H + BRICK_GAP)
        bricks.append((pg.Rect(x, y, BRICK_W, BRICK_H),
                      BRICK_COLORS[row % len(BRICK_COLORS)]))

# --------------------- PADDLE, BALL & GAME STATE ---------------------
paddle   = pg.Rect((W - PADDLE_W)//2, H - 60, PADDLE_W, PADDLE_H)
ball_pos = pg.Vector2(paddle.centerx, paddle.top - BALL_R - 1)
ball_vel = pg.Vector2(random.choice([-1, 1]), -1).normalize() * BALL_SPEED
playing, won = True, False

def reset():
    global ball_pos, ball_vel, bricks, playing, won
    bricks.clear()
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = BRICK_GAP + col * (BRICK_W + BRICK_GAP)
            y = top_offset + row * (BRICK_H + BRICK_GAP)
            bricks.append((pg.Rect(x, y, BRICK_W, BRICK_H),
                           BRICK_COLORS[row % len(BRICK_COLORS)]))
    paddle.centerx = W//2
    ball_pos.update(paddle.centerx, paddle.top - BALL_R - 1)
    ball_vel.update(random.choice([-1, 1]), -1)
    ball_vel.scale_to_length(BALL_SPEED)
    playing, won = True, False

# ------------------------------ MAIN LOOP ----------------------------
while True:
    # ----- events -----
    for ev in pg.event.get():
        if ev.type == pg.QUIT: 
            pg.quit(); sys.exit()
        if ev.type == pg.KEYDOWN and ev.key in (pg.K_ESCAPE, pg.K_q):
            pg.quit(); sys.exit()
        if ev.type == pg.KEYDOWN and not playing and ev.key == pg.K_r:
            reset()

    # ----- input -----
    keys = pg.key.get_pressed()
    if keys[pg.K_LEFT]:
        paddle.x -= 9
    if keys[pg.K_RIGHT]:
        paddle.x += 9
    paddle.clamp_ip(screen.get_rect())

    # ----- update -----
    if playing:
        ball_pos += ball_vel
        ball = pg.Rect(int(ball_pos.x) - BALL_R,
                       int(ball_pos.y) - BALL_R,
                       BALL_R*2, BALL_R*2)

        # walls
        if ball.left <= 0 or ball.right >= W:
            ball_vel.x *= -1
            ball_pos.x = max(ball_pos.x, BALL_R)
            ball_pos.x = min(ball_pos.x, W - BALL_R)
            SFX_WALL.play()
        if ball.top <= 0:
            ball_vel.y *= -1
            ball_pos.y = BALL_R
            SFX_WALL.play()

        # paddle
        if ball.colliderect(paddle) and ball_vel.y > 0:
            overlap = (ball.centerx - paddle.centerx) / (PADDLE_W / 2)
            angle   = overlap * 60
            speed   = ball_vel.length()
            ball_vel.from_polar((speed, -angle))
            ball_pos.y = paddle.top - BALL_R - 1
            SFX_PADDLE.play()

        # bricks
        for rect, color in bricks[:]:
            if ball.colliderect(rect):
                bricks.remove((rect, color))
                if abs(ball.centerx - rect.left) < BALL_R or \
                   abs(ball.centerx - rect.right) < BALL_R:
                    ball_vel.x *= -1
                else:
                    ball_vel.y *= -1
                SFX_BRICK.play()
                break

        # lose / win
        if ball.top >= H:
            playing = False
            SFX_LOSE.play()
        if not bricks and playing:
            playing = False
            won = True
            SFX_WIN.play()

    # ----- render -----
    screen.fill(BG_COLOR)
    for rect, color in bricks:
        pg.draw.rect(screen, color, rect, border_radius=4)
    pg.draw.rect(screen, PADDLE_COLOR, paddle, border_radius=6)
    pg.draw.circle(screen, BALL_COLOR, ball_pos, BALL_R)

    if playing:
        txt = font.render(f"Bricks left: {len(bricks)}", True, FONT_COLOR)
        screen.blit(txt, (10, 10))
    else:
        msg = "YOU WIN!  Press R to replay" if won else "GAME OVER  Press R to retry"
        txt = font.render(msg, True, FONT_COLOR)
        screen.blit(txt, txt.get_rect(center=(W//2, H//2)))

    pg.display.flip()
    clock.tick(FPS)
