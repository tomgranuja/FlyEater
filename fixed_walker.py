#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import csv
import sys
import random
import pygame
import numpy as np

pygame.init()
GAME_FPS = 30
REWARD_MILLS = 5000
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

class Jumper(Soul):
    XVEL = 150
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
        self.jump_data = {}
            
    def load_jump_data(self, path, yoffset=0, framerange=None, reverse=True):
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            data = { int(row['frame']): 
                        (int(row['y']) - yoffset)*self.DATA_FACTOR
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
    
    def update(self):
        keys = pygame.key.get_pressed()
        self._pos[0] += self.XVEL/GAME_FPS
        if self._pos[0] > W:
           self._pos[0] = .0 
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

player1 = Jumper()
player1.load_jump_data('posicion_fixed.csv', 0, (1,120), reverse=False)
player1.set_kbd_dic()
players = pygame.sprite.Group(player1)
all_sprites = pygame.sprite.Group(players)
screen.blit(background,(0,0))

while True:
        #Erase objects using the background
    for o in all_sprites:
        screen.blit(background, o.rect, o.rect)
    #Catch quit event and exit
    for e in pygame.event.get():
        if e.type == pygame.QUIT: sys.exit()
    #Move objects
    for o in all_sprites:
        o.update()
    #Paint objects
    all_sprites.draw(screen)
    pygame.display.update()
    #Overall game frames per second
    clock.tick(GAME_FPS)

#if __name__ == '__main__':
#    pass
