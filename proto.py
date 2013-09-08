#!/usr/bin/python3
import sys
import pygame
import operator
import random
from pygame.locals import *

BLACK = 0, 0, 0
BLUE = 0, 0, 255
GRAY = 80, 80, 80
WHITE = 255, 255, 255
RED = 255, 0, 0
YELLOW = 255, 255, 0

SCREEN_SIZE = 640, 480
LEVEL_SPEED = 0.3
PLATFORM_SIZE = 50, 60
PLATFORM_HP = 100
PLATFORM_DAMAGE = 65535
ENEMY_HP = 30
ENEMY_DAMAGE = 30
ENEMY_SIZE = 40, 50
ENEMY_SPEED = 0.0
WALL_SIZE = 50, SCREEN_SIZE[1]
BULLET_SIZE = 10, 10
BULLET_SPEED = 2
BULLET_DAMAGE = 10
PLAYER_SHOOTING_DELAY = 100
ENEMY_SHOOTING_DELAY = 1000
START_POS = 320, 420
BONUS_SIZE = 32, 32

class Object:
	def __init__(self, pos, size, color):
		self.surface = pygame.surface.Surface(size)
		self.surface.fill(color)
		self.pos = list(pos)
		self.alive = True

	def shoot(self):
		return []

	def collide_with(self, other):
		pass

	def get_rect(self):
		rect = self.surface.get_rect()
		rect.center = tuple(map(int, self.pos))
		return rect

class PlayerBullet(Object):
	def __init__(self, pos):
		Object.__init__(self, pos, BULLET_SIZE, BLUE)

	def collide_with(self, other):
		if isinstance(other, Enemy):
			self.alive = False

	def move(self):
		self.pos[1] -= BULLET_SPEED

class EnemyBullet(Object):
	def __init__(self, pos):
		Object.__init__(self, pos, BULLET_SIZE, RED)

	def collide_with(self, other):
		if isinstance(other, Platform):
			self.alive = False

	def move(self):
		self.pos[1] += BULLET_SPEED

class ShootingObject(Object):
	def __init__(self, pos, size, color, shooting_delay, bullet_type):
		Object.__init__(self, pos, size, color)
		self.max_shooting_delay, self.bullet_type = shooting_delay, bullet_type
		self.shooting_delay = 0

	def _shoot(self, shooting=True):
		bullets = []
		if shooting and self.shooting_delay <= 0:
			bullets.append(self.bullet_type(self.pos))
			self.shooting_delay = self.max_shooting_delay
		if self.shooting_delay > 0:
			self.shooting_delay -= 1
		return bullets

class PlayerController:
	def __init__(self, rects):
		self.rects = rects
		self.shift = 0
		self.shooting = False

class Platform(ShootingObject):
	def __init__(self, pos, controller):
		ShootingObject.__init__(self, pos, PLATFORM_SIZE, BLUE, PLAYER_SHOOTING_DELAY, PlayerBullet)
		self.controller = controller
		self.max_hp = PLATFORM_HP
		self.hp = self.max_hp

	def collide_with(self, other):
		if isinstance(other, Enemy):
			self.hp -= ENEMY_DAMAGE
		elif isinstance(other, EnemyBullet):
			self.hp -= BULLET_DAMAGE
		if self.hp <= 0:
			self.alive = False

	def move(self):
		old_pos = self.pos[0]
		self.pos[0] += self.controller.shift
		if self.get_rect().collidelist(self.controller.rects) != -1:
			self.pos[0] = old_pos

	def shoot(self):
		return self._shoot(self.controller.shooting)

class Enemy(ShootingObject):
	def __init__(self, pos):
		ShootingObject.__init__(self, pos, ENEMY_SIZE, RED, ENEMY_SHOOTING_DELAY, EnemyBullet)
		self.max_hp = ENEMY_HP
		self.hp = self.max_hp

	def collide_with(self, other):
		if isinstance(other, Platform):
			self.hp -= PLATFORM_DAMAGE
		elif isinstance(other, PlayerBullet):
			self.hp -= BULLET_DAMAGE
		if self.hp <= 0:
			self.alive = False

	def shoot(self):
		return self._shoot()

	def move(self):
		self.pos[1] += LEVEL_SPEED + ENEMY_SPEED

class Bonus(Object):
	def __init__(self, pos):
		Object.__init__(self, pos, BONUS_SIZE, YELLOW)

	def collide_with(self, other):
		if isinstance(other, Platform):
			self.alive = False

	def move(self):
		self.pos[1] += LEVEL_SPEED


pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
font = pygame.font.SysFont(None, 24)

wall_left = pygame.surface.Surface(WALL_SIZE)
wall_left.fill(GRAY)
wall_left_rect = wall_left.get_rect()
wall_left_rect.topleft = 0, 0

wall_right = pygame.surface.Surface(WALL_SIZE)
wall_right.fill(GRAY)
wall_right_rect = wall_right.get_rect()
wall_right_rect.topright = SCREEN_SIZE[0], 0

level_map = []
level_map += [(Enemy, i * 500, 100 + i * 25) for i in range(20)]
level_map += [(Bonus, 100 + i * 1000, random.randrange(wall_left_rect.right + BONUS_SIZE[0]/2, wall_right_rect.left - BONUS_SIZE[0]/2)) for i in range(5)]

player = PlayerController([wall_left_rect, wall_right_rect])

platform_count = 3
level_pos = 0
platform = Platform(START_POS, player)
objects = [platform]

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			if event.key == K_q or event.key == K_ESCAPE:
				sys.exit()
	player.shift = pygame.mouse.get_rel()[0]
	player.shooting = any(pygame.mouse.get_pressed())

	# Logic.
	level_pos += LEVEL_SPEED

	for object_type, map_pos, screen_pos in level_map:
		if map_pos < level_pos:
			objects.append(object_type((screen_pos, 0)))
	level_map = [(object_type, map_pos, screen_pos) for object_type, map_pos, screen_pos in level_map if map_pos > level_pos]

	new_objects = []
	for o in objects:
		o.move()
		new_objects += o.shoot()
	objects += new_objects

	for a in objects:
		for b in objects:
			if a.get_rect().colliderect(b.get_rect()):
				a.collide_with(b)

	objects = [o for o in objects if o.alive and 0 < o.get_rect().bottom and o.get_rect().top < SCREEN_SIZE[1]]
	if not platform.alive:
		platform_count -= 1
		platform = Platform(START_POS, player)
		objects.append(platform)
		if platform_count < 0:
			sys.exit()

	# Drawing.
	screen.fill(BLACK)
	screen.blit(wall_left, wall_left_rect)
	screen.blit(wall_right, wall_right_rect)
	for o in objects:
		screen.blit(o.surface, o.get_rect())

	hud = ["Level: {0:10.2f}; {2}x {3}/{4}hp, {1}".format(level_pos, "shooting" if player.shooting else "", platform_count, platform.hp, platform.max_hp)]
	for o in objects:
		hud.append("{0}: ({1:0.2f},{2:#0.2f})".format(o.__class__.__name__, o.pos[0], o.pos[1]))
	for number, line in enumerate(hud):
		screen.blit(font.render(line, True, WHITE), (wall_left_rect.right, number * font.get_height()))

	pygame.display.flip()
