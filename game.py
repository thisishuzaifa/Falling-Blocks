import pygame
import random
import sys



# Initializing pygame
pygame.init()



# Window resolution
WIDTH = 1024
HEIGHT = 768



# Color Grid
RED = (178,34,34)
BLUE = (65,105,225)
YELLOW = (255,255,0)
BACKGROUND_COLOR = (139,137,137)



# Player block Size and Position
player_size = 50
player_pos = [WIDTH/2, HEIGHT-2*player_size]


# Block size position and list 
block_size = 50
block_position = [random.randint(0,WIDTH-block_size), 0]
block_list = [block_position]


# Game speed
SPEED = 10

screen = pygame.display.set_mode((WIDTH, HEIGHT))

game_over = False

score = 0

clock = pygame.time.Clock()


# Font style for the game
font_style = pygame.font.SysFont("monospace", 35)


# Level and speed increases as player advances
def set_level(score, SPEED):
	''' This function sets the speed and score '''
	if score < 20:
		SPEED = 5
	elif score < 40:
		SPEED = 8
	elif score < 60:
		SPEED = 12
	else:
		SPEED = 15
	return SPEED
	# SPEED = score/5 + 1

# Function for falling blocks, which is random
def block_fall(block_list):
	''' This function regulates how the blocks fall '''
	delay = random.random()
	if len(block_list) < 10 and delay < 0.1:
		x_pos = random.randint(0,WIDTH-block_size)
		y_pos = 0
		block_list.append([x_pos, y_pos])
# Funciton to draw
def draw_block(block_list):
	''' This function generates blocks '''
	for block_position in block_list:
		pygame.draw.rect(screen, BLUE, (block_position[0], block_position[1], block_size, block_size))

def update_block_positionitions(block_list, score):
	''' This function updates the position, increases the speed and keeps trach of score counter '''
	for idx, block_position in enumerate(block_list):
		if block_position[1] >= 0 and block_position[1] < HEIGHT:
			block_position[1] += SPEED
		else:
			block_list.pop(idx)
			score += 1
	return score

def check_impact(block_list, player_pos):
	''' This funcion checks for impact with other blocks'''
	for block_position in block_list:
		if find_impact(block_position, player_pos):
			return True
	return False

def find_impact(player_pos, block_position):
	''' This fucntions finds the impact and terminates the game'''
	p_x = player_pos[0]
	p_y = player_pos[1]

	e_x = block_position[0]
	e_y = block_position[1]

	if (e_x >= p_x and e_x < (p_x + player_size)) or (p_x >= e_x and p_x < (e_x+block_size)):
		if (e_y >= p_y and e_y < (p_y + player_size)) or (p_y >= e_y and p_y < (e_y+block_size)):
			return True
	return False

while not game_over:

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()

		if event.type == pygame.KEYDOWN:

			x = player_pos[0]
			y = player_pos[1]

			if event.key == pygame.K_LEFT:
				x -= player_size
			elif event.key == pygame.K_RIGHT:
				x += player_size

			player_pos = [x,y]

	screen.fill(BACKGROUND_COLOR)
	
	block_fall(block_list)
	score = update_block_positionitions(block_list, score)
	SPEED = set_level(score, SPEED)

	text = "Score:" + str(score) 
	label = font_style.render(text, 1, YELLOW)
	screen.blit(label, (WIDTH-200, HEIGHT-40))


	if check_impact(block_list, player_pos):
		game_over = True
		break

	draw_block(block_list)

	pygame.draw.rect(screen, RED, (player_pos[0], player_pos[1], player_size, player_size))

	clock.tick(30)

	pygame.display.update()
