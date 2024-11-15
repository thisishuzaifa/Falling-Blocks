import pygame
import random
import sys
from enum import Enum


class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3


class Colors:
    CORAL = (255, 127, 80)
    TEAL = (0, 128, 128)
    MUSTARD = (255, 204, 0)
    MINT = (152, 255, 152)
    OFF_WHITE = (245, 245, 245)
    BACKGROUND = (40, 44, 52)


class Config:
    WIDTH = 1280
    HEIGHT = 720
    FPS = 60
    PLAYER_SIZE = 50
    BLOCK_SIZE = 50
    INITIAL_SPEED = 5
    LIVES = 3


class Player:
    def __init__(self):
        self.size = Config.PLAYER_SIZE
        self.speed = 10
        self.velocity = 0
        self.reset_position()

    def reset_position(self):
        self.pos = [Config.WIDTH // 2, Config.HEIGHT - 2 * self.size]

    def move(self, direction):
        self.velocity = direction * self.speed

    def stop(self):
        self.velocity = 0

    def update(self):
        self.pos[0] = max(0, min(Config.WIDTH - self.size, self.pos[0] + self.velocity))

    def draw(self, screen):
        pygame.draw.rect(screen, Colors.CORAL, (self.pos[0], self.pos[1], self.size, self.size))


class Block:
    def __init__(self):
        self.size = Config.BLOCK_SIZE
        self.reset()

    def reset(self):
        self.pos = [random.randint(0, Config.WIDTH - self.size), 0]

    def update(self, speed):
        self.pos[1] += speed

    def is_off_screen(self):
        return self.pos[1] >= Config.HEIGHT

    def draw(self, screen):
        pygame.draw.rect(screen, Colors.TEAL, (self.pos[0], self.pos[1], self.size, self.size))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Falling Blocks - Huzaifa Khalid")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 35)
        self.big_font = pygame.font.SysFont("monospace", 70)

        self.player = Player()
        self.blocks = []
        self.reset_game()

        self.state = GameState.MENU

    def reset_game(self):
        self.player.reset_position()
        self.blocks.clear()
        self.score = 0
        self.speed = Config.INITIAL_SPEED
        self.lives = Config.LIVES

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_LEFT:
                        self.player.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1)
                    elif event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                elif event.key == pygame.K_SPACE:
                    if self.state == GameState.MENU:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.GAME_OVER:
                        self.reset_game()
                        self.state = GameState.PLAYING
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        self.state = GameState.PLAYING

            if event.type == pygame.KEYUP:
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.player.stop()

        return True

    def update(self):
        if self.state != GameState.PLAYING:
            return

        self.player.update()

        # Spawn new blocks
        if len(self.blocks) < 10 and random.random() < 0.1:
            self.blocks.append(Block())

        # Update blocks and check for scoring
        for block in self.blocks[:]:
            block.update(self.speed)
            if block.is_off_screen():
                self.blocks.remove(block)
                self.score += 1

        # Update speed based on score
        self.speed = 5 + (self.score // 10)

        # Check for collisions
        player_rect = pygame.Rect(self.player.pos[0], self.player.pos[1], self.player.size, self.player.size)
        for block in self.blocks:
            block_rect = pygame.Rect(block.pos[0], block.pos[1], block.size, block.size)
            if player_rect.colliderect(block_rect):
                self.lives -= 1
                self.blocks.remove(block)
                if self.lives == 0:
                    self.state = GameState.GAME_OVER

    def draw(self):
        self.screen.fill(Colors.BACKGROUND)

        if self.state == GameState.MENU:
            self.draw_text("FALLING BLOCKS", self.big_font, Colors.MUSTARD, Config.WIDTH // 2, Config.HEIGHT // 3)
            self.draw_text("Press SPACE to start", self.font, Colors.OFF_WHITE, Config.WIDTH // 2, Config.HEIGHT // 2)
        elif self.state == GameState.GAME_OVER:
            self.draw_text("GAME OVER", self.big_font, Colors.CORAL, Config.WIDTH // 2, Config.HEIGHT // 3)
            self.draw_text(f"Final Score: {self.score}", self.font, Colors.OFF_WHITE, Config.WIDTH // 2, Config.HEIGHT // 2)
            self.draw_text("Press SPACE to restart", self.font, Colors.OFF_WHITE, Config.WIDTH // 2, Config.HEIGHT * 2 // 3)
        elif self.state == GameState.PAUSED:
            self.draw_text("PAUSED", self.big_font, Colors.MUSTARD, Config.WIDTH // 2, Config.HEIGHT // 3)
            self.draw_text("Press P to resume", self.font, Colors.OFF_WHITE, Config.WIDTH // 2, Config.HEIGHT // 2)

        if self.state in (GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER):
            self.player.draw(self.screen)
            for block in self.blocks:
                block.draw(self.screen)

            score_text = f"Score: {self.score}"
            level_text = f"Level: {self.speed - 4}"
            lives_text = f"Lives: {self.lives}"
            self.draw_text(score_text, self.font, Colors.MUSTARD, Config.WIDTH - 100, 30)
            self.draw_text(level_text, self.font, Colors.MINT, Config.WIDTH - 100, 70)
            self.draw_text(lives_text, self.font, Colors.CORAL, Config.WIDTH - 100, 110)

        pygame.display.flip()

    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.centerx = x
        text_rect.y = y
        self.screen.blit(text_surface, text_rect)

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
