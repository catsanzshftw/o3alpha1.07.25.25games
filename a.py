#!/usr/bin/env python3
"""
Grand Vibe Auto: o3-alpha – One Shott (Mac Safe)
Zero-asset, 60 FPS, pure Pygame HUD, day/night, single file, VIBES MODE ON.
"""

import pygame, sys, random, math, time

class E:
    def __init__(s,x,y,w,h,c,sp=0,a=''):s.x,s.y,s.w,s.h,s.c,s.s,s.a,s.d,s.cd=x,y,w,h,c,sp,a,random.choice([(1,0),(-1,0),(0,1),(0,-1)]),0
    def r(s): return pygame.Rect(s.x,s.y,s.w,s.h)
    def m(s):
        if s.a=='car':
            s.x+=s.d[0]*s.s;s.y+=s.d[1]*s.s
            if s.x<0 or s.x>860:s.d=(-s.d[0],s.d[1])
            if s.y<0 or s.y>560:s.d=(s.d[0],-s.d[1])
        elif s.a=='cop':
            dx,dy=player.x-s.x,player.y-s.y;d=max(1,math.hypot(dx,dy))
            s.x+=(dx/d)*s.s;s.y+=(dy/d)*s.s

WIDTH,HEIGHT,FPS=900,600,60
COL={'P':(48,200,255),'COP':(255,32,64),'CAR':(232,224,48),'ROAD':(80,80,80),'BG':(32,160,32)}
NIGHT=(16,32,64,170);DAY=(255,220,144,24)
pygame.init()
screen=pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Grand Vibe Auto o3α")
font=pygame.font.SysFont("Consolas",25,1)
clock=pygame.time.Clock()
player=E(WIDTH//2,HEIGHT//2,32,24,COL['P'],6)
cars=[E(random.randint(60,840),random.randint(60,540),32,24,COL['CAR'],2,'car')for _ in range(8)]
cops=[];wanted=0;score=0;hp=100;lhit=0

def vibe_light(t):
    if t<0.5:ra,rb=t*2,1-t*2
    else:ra,rb=(t-0.5)*2,1-(t-0.5)*2
    if t<0.5:
        a=int(NIGHT[3]*rb+DAY[3]*ra);r=int(NIGHT[0]*rb+DAY[0]*ra)
        g=int(NIGHT[1]*rb+DAY[1]*ra);b=int(NIGHT[2]*rb+DAY[2]*ra)
    else:
        a=int(DAY[3]*rb+NIGHT[3]*ra);r=int(DAY[0]*rb+NIGHT[0]*ra)
        g=int(DAY[1]*rb+NIGHT[1]*ra);b=int(DAY[2]*rb+NIGHT[2]*ra)
    return (r,g,b,a)

def draw_hud():
    txt=font.render(f"HP:{max(0,hp)}  Score:{score}  Wanted:{'★'*wanted}{' '*(3-wanted)}",1,(250,250,250))
    screen.blit(txt,(18,8))
    screen.blit(font.render("VIBES MODE: ON",1,(255,128,255)),(WIDTH-245,HEIGHT-38))
    screen.blit(font.render("Grand Vibe Auto (o3-alpha)",1,(120,255,255)),(10,HEIGHT-42))
    screen.blit(font.render("WASD/Arrows: Move  |  Esc: Quit",1,(220,220,180)),(10,HEIGHT-20))

run=1
while run:
    dt=clock.tick(FPS)/1e3;t=(time.time()/15)%1.0
    screen.fill(COL['BG'])
    for y in range(60,HEIGHT,120):pygame.draw.rect(screen,COL['ROAD'],(0,y,WIDTH,48))
    for x in range(60,WIDTH,120):pygame.draw.rect(screen,COL['ROAD'],(x,0,48,HEIGHT))
    for c in cars:c.m();pygame.draw.rect(screen,c.c,c.r(),border_radius=6)
    for cop in cops:cop.m();pygame.draw.rect(screen,cop.c,cop.r(),border_radius=8)
    k=pygame.key.get_pressed();vx=vy=0
    if k[pygame.K_w]or k[pygame.K_UP]:vy=-player.s
    if k[pygame.K_s]or k[pygame.K_DOWN]:vy=player.s
    if k[pygame.K_a]or k[pygame.K_LEFT]:vx=-player.s
    if k[pygame.K_d]or k[pygame.K_RIGHT]:vx=player.s
    player.x=max(0,min(WIDTH-player.w,player.x+vx))
    player.y=max(0,min(HEIGHT-player.h,player.y+vy))
    pygame.draw.rect(screen,player.c,player.r(),border_radius=10)
    now=time.time()
    for c in cars:
        if player.r().colliderect(c.r()) and now-lhit>0.6:
            hp-=8;score-=2;wanted=min(3,wanted+1);lhit=now
            if len(cops)<wanted*2:
                for _ in range(wanted):cops.append(E(random.randint(20,WIDTH-60),random.randint(20,HEIGHT-60),36,28,COL['COP'],2.7+0.5*wanted,'cop'))
    for cop in cops:
        if player.r().colliderect(cop.r()) and now-lhit>0.7:hp-=18;score-=5;lhit=now
    cops=[c for c in cops if 0<=c.x<WIDTH and 0<=c.y<HEIGHT]
    surf=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);surf.fill(vibe_light(t));screen.blit(surf,(0,0))
    draw_hud()
    for e in pygame.event.get():
        if e.type==pygame.QUIT or(e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):run=0
    if hp<=0:
        screen.blit(font.render("GAME OVER! (Esc to Quit)",1,(255,64,64)),(WIDTH//2-170,HEIGHT//2-22))
        pygame.display.flip();pygame.time.wait(1500);run=0;break
    pygame.display.flip()
pygame.quit();sys.exit()
