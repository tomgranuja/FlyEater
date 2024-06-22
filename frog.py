#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import csv
import sys
import random
import pygame
import numpy as np

pygame.init()
GAME_FPS = 70
REWARD_MILLS = 5000
N_FLYS = 20
clock = pygame.time.Clock()
#Width and height of the game
size = W,H = 1000, 720
#Screen, background and player surfaces
screen = pygame.display.set_mode(size)
screen.fill((255,)*3)
background = pygame.image.load('background.png').convert()
GROUNDY = 646
BLACK = (0, 0, 0)

class Soul(pygame.sprite.Sprite):
    def __init__(self, img_path, offset=(0,0)):
        super().__init__()
        self.image = pygame.image.load(img_path).convert_alpha()
        self.pos = self.image.get_rect().move(*offset)
        self.rect = self.pos
        
    #Transform self.pos in a property in order to
    #use float precition in the x and y coordinates.
    @property
    def pos(self):
        x,y,w,h = self._pos
        #Return rounded x and y coordinates Rect.
        return pygame.Rect(round(x), round(y), w, h)
    
    @pos.setter
    def pos(self,o):
        x,y,w,h = o
        #Store as a float list.
        self._pos = [x,y,w,h]

class Ball(Soul):
    
    def __init__(self, xvel, from_left=False):
        super().__init__('circle_M.png')
        self.rect.bottom = GROUNDY
        if from_left:
            self.rect.right = 0
        else:
            xvel = -xvel
            self.rect.left = W
        self.pos = self.rect
        self.xvel = xvel
    
    def update(self):
        self._pos[0] += self.xvel/GAME_FPS
        self.rect = self.pos
        x,y,w,h = self.rect
        if x < -w or x > W :
            self.kill()
            
class Fly(Soul):
    VEL = 0.5
    MARGIN = 10
    DESVEST = 0.03
    
    def __init__(self):
        offset = (random.randrange(self.MARGIN, W - self.MARGIN),
                  random.randrange(self.MARGIN, GROUNDY - self.MARGIN))
        super().__init__('fly.png', offset)
        self.angle = random.uniform(0, 2*np.pi)
    
    def update(self):
        x,y,w,h = self._pos
        step = np.array((np.cos(self.angle), np.sin(self.angle))) * self.VEL
        x,y = step + (x,y)
        self._pos = (x,y,w,h)
        self.rect = self.pos
        if self.outside():
            self.kill()
        self.angle += random.gauss(mu=0, sigma=self.DESVEST*2*np.pi)
    
    def outside(self):
        rect = self.rect
        outside_x = (rect.left > W) or (rect.right < 0)
        outside_y = (rect.bottom < 0) or (rect.centery > GROUNDY)
        return outside_x or outside_y


class Jumper(Soul):
    XVEL = 350
    JUMPING_MILLS = 1000
    INITIAL_POINTS = 180
    DATA_FPS = 60
    DATA_FACTOR = 1.5
    
    def __init__(self, xpos=W/5):
        super().__init__('frog_ground.png', (xpos, 0))
        self.xpos = xpos
        self.rect.bottom = GROUNDY
        self.pos = self.rect
        self.jump_mills = 0
        self.jumping = False
        self.points = self.INITIAL_POINTS
        self.draw_points()
        self.jump_data = {}
            
    def load_jump_data(self, path, yoffset=0, framerange=None, reverse=True):
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            data = { int(row['frame']): 
                        (int(row['frog_y']) - yoffset)*self.DATA_FACTOR
                     for row in reader }
            if framerange is not None:
                data = {k - framerange[0] : data[k]
                        for k in data
                        if framerange[0] <= k <= framerange[1]}
            if reverse:
                maxkey = max(data.keys())
                data = {maxkey-k : data[k]
                        for k in data}
            self.jump_data = data
        
    def draw_points(self, surface=None):
        font = pygame.font.SysFont("serif", 24)
        self.points_surface = font.render(str(self.points), True, BLACK)
        self.points_rect = self.points_surface.get_rect()
        self.points_rect.midbottom = self.rect.midtop
        self.points_rect.bottom -= 5
        if surface is not None:
            surface.blit(self.points_surface, self.points_rect)
    
    def update(self):
        keys = pygame.key.get_pressed()
        #2-dimensional vectors
        u = np.ones(2)
        i = u*(1,0)
        # j = u*(0,-1)
        vector = sum([  i*keys[self.k['r']],
                    -i*keys[self.k['l']] ])
                    #     j*keys[self.k['u']],
                    # -j*keys[self.k['d']],
                    # ])
        self._pos[0] += self.XVEL/GAME_FPS * vector[0]
        self.rect = self.pos
        
        now = pygame.time.get_ticks()
        mills = now - self.jump_mills
        frame = mills // (1000 * 1/self.DATA_FPS)
        if self.jump_data:
            over_data = frame > max(self.jump_data.keys())
        else:
            over_data = mills > self.JUMPING_MILLS
        if over_data:
            self.end_jump()
            self.jumping = False
        
        if keys[self.k['u']]:
            if not self.jumping:
                self.start_jump()
                self.jump_mills = now
                self.jumping = True
        
        if self.jumping:
            if frame in self.jump_data:
                #Could use self.pos to use float precition
                x,y,w,h = self._pos
                y = GROUNDY - h - self.jump_data[frame]
                self.pos = x,y,w,h
                self.rect = self.pos
                
    def start_jump(self):
        self.image = pygame.image.load('frog_air.png').convert_alpha()
        self.rect = self.image.get_rect().move(self.rect.topleft)
        self.rect.bottom = GROUNDY
        if not self.jump_data:
            self.rect.bottom = GROUNDY - 100
        self.pos = self.rect
        
    def end_jump(self):
        self.image = pygame.image.load('frog_ground.png').convert_alpha()
        self.rect = self.image.get_rect().move(self.rect.topleft)
        self.rect.bottom = GROUNDY
        self.pos = self.rect
    
    def set_kbd_dic(self, **kwargs):
        k = { 'r': pygame.K_RIGHT,
              'l': pygame.K_LEFT,
              'u': pygame.K_UP,
            }
        k.update(kwargs)
        self.k = { key: k[key] for key in 'rlu' }
        
    def hit(self):
        self.points -= 100
        self.rect.left = self.xpos
        self.pos = self.rect
        if self.points < 0:
            self.kill()
    
    def eat(self):
        self.points += 10

player1 = Jumper()
player1.load_jump_data('posicion_salva.csv', 90, (1,93), reverse=False)
player2 = Jumper()
player2.load_jump_data('posicion_cris.csv', 155, (1,182), reverse=False)
# player1 = Jumper()
# player2 = Jumper()
player1.set_kbd_dic()
player2.set_kbd_dic(r=pygame.K_d,
                    l=pygame.K_a,
                    u=pygame.K_w,)
players = pygame.sprite.Group(player1, player2)
balls = pygame.sprite.Group(Ball(80))
flys = pygame.sprite.Group([Fly() for _ in range(N_FLYS)])
last_add_ball_millis = pygame.time.get_ticks()
all_sprites = pygame.sprite.Group(players, balls, flys)
screen.blit(background,(0,0))

def add_ball(time_offset=1000):
    now_millis = pygame.time.get_ticks()
    if now_millis - last_add_ball_millis > time_offset:
        if random.random() > 0.8:
            ball = Ball(random.gauss(80, 20))
            ball.add(balls, all_sprites)
        return now_millis
    return last_add_ball_millis


from_reward_mills = 0
while True:
    frame_mills = pygame.time.get_ticks()
    #Erase objects using the background
    for o in all_sprites:
        screen.blit(background, o.rect, o.rect)
    for p in players:
        screen.blit(background, p.points_rect, p.points_rect)
    #Catch quit event and exit
    for e in pygame.event.get():
        if e.type == pygame.QUIT: sys.exit()
    #Add flys
    if len(flys) < N_FLYS:
     Fly().add(flys, all_sprites)
    #Add ball
    last_add_ball_millis = add_ball()
    #Move objects
    for o in all_sprites:
        o.update()
    #Give points
    if (frame_mills - from_reward_mills) > REWARD_MILLS:
        from_reward_mills = frame_mills
        for p in players:
            p.points += 20
    #Chequear colisiones entre cada player y balls/fly
    for p in players:
        hits = pygame.sprite.spritecollide(p, balls, dokill=True)
        [p.hit() for hit in hits]
        hits = pygame.sprite.spritecollide(p, flys, dokill=True)
        [p.eat() for hit in hits]
    
    #Paint objects
    all_sprites.draw(screen)
    for p in players:
        p.draw_points(screen)
    pygame.display.update()
    print(pygame.time.get_ticks()/1000, *flys.sprites()[0].rect.center)
    #Overall game frames per second
    clock.tick(GAME_FPS)

#if __name__ == '__main__':
#    pass
