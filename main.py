import pygame
import random
import sys
import math
from enum import Enum, auto
import asyncio


class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    HIGH_SCORES = 4


class BlockType(Enum):
    NORMAL = 0
    HARMFUL = 1
    BONUS = 2
    POWER_UP = 3


class PowerUpType(Enum):
    SHIELD = auto()
    SLOW_TIME = auto()
    MAGNET = auto()
    EXTRA_LIFE = auto()


class Colors:
    CORAL = (255, 127, 80)
    TEAL = (0, 128, 128)
    MUSTARD = (255, 204, 0)
    MINT = (152, 255, 152)
    OFF_WHITE = (245, 245, 245)
    BACKGROUND = (20, 24, 35)
    LIGHT_BLUE = (100, 200, 255)
    PURPLE = (150, 100, 250)
    RED = (255, 80, 80)
    GREEN = (80, 240, 80)
    DARK_TEAL = (0, 80, 80)
    GOLD = (255, 215, 0)
    PARTICLES = [(255, 255, 255), (255, 200, 100), (100, 200, 255), (200, 100, 255)]
    SHIELD = (100, 150, 255, 100)  # With alpha


class Config:
    WIDTH = 1280
    HEIGHT = 720
    FPS = 60
    PLAYER_SIZE = 50
    BLOCK_SIZE = 50
    INITIAL_SPEED = 5
    LIVES = 3
    BLOCK_SPAWN_RATE = 0.1
    MAX_BLOCKS = 15
    POWER_UP_CHANCE = 0.05
    HIGH_SCORES_COUNT = 5
    SHIELD_DURATION = 5 * FPS  # 5 seconds
    SLOW_TIME_DURATION = 3 * FPS  # 3 seconds
    MAGNET_DURATION = 7 * FPS  # 7 seconds
    MAGNET_RADIUS = 200
    PARTICLE_LIFE = 30
    ANIMATION_SPEED = 0.1
    MIN_WIDTH = 1280  # Minimum width
    MIN_HEIGHT = 720  # Minimum height


class Particle:
    def __init__(self, x, y, color, velocity_x=0, velocity_y=0, size=5, life=None):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.size = size
        self.initial_size = size
        self.life = life if life else Config.PARTICLE_LIFE
        self.max_life = self.life

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.life -= 1
        self.size = self.initial_size * (self.life / self.max_life)
        return self.life > 0

    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color[:3], alpha), (self.size, self.size), self.size)
        screen.blit(s, (self.x - self.size, self.y - self.size))


class Player:
    def __init__(self):
        self.size = Config.PLAYER_SIZE
        self.speed = 10
        self.velocity = 0
        self.trail = []
        self.active_powers = {
            PowerUpType.SHIELD: 0,
            PowerUpType.SLOW_TIME: 0,
            PowerUpType.MAGNET: 0
        }
        self.angle = 0  # For rotation animation
        self.pulse = 0  # For pulsating animation
        self.reset_position()

    def reset_position(self):
        self.pos = [Config.WIDTH // 2, Config.HEIGHT - 2 * self.size]
        self.trail.clear()
        self.active_powers = {power: 0 for power in self.active_powers}

    def move(self, direction):
        self.velocity = direction * self.speed

    def stop(self):
        self.velocity = 0

    def has_power(self, power_type):
        return self.active_powers.get(power_type, 0) > 0

    def activate_power(self, power_type, duration):
        self.active_powers[power_type] = duration

    def update(self):
        old_x = self.pos[0]
        self.pos[0] = max(0, min(Config.WIDTH - self.size, self.pos[0] + self.velocity))
        
        # Add trail particles if moving
        if abs(self.velocity) > 0 and random.random() < 0.3:
            color = random.choice(Colors.PARTICLES)
            self.trail.append(
                Particle(
                    self.pos[0] + self.size // 2,
                    self.pos[1] + self.size // 2,
                    color,
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 3),
                    random.randint(3, 6)
                )
            )
        
        # Update trail
        self.trail = [p for p in self.trail if p.update()]
        
        # Update power timers
        for power in list(self.active_powers.keys()):
            if self.active_powers[power] > 0:
                self.active_powers[power] -= 1
        
        # Update animations
        self.angle = (self.angle + Config.ANIMATION_SPEED * abs(self.velocity) * 0.2) % 360
        self.pulse = (self.pulse + Config.ANIMATION_SPEED) % (2 * math.pi)

    def draw(self, screen):
        # Draw trail
        for particle in self.trail:
            particle.draw(screen)
        
        # Draw player shape
        player_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Change player shape based on status
        if self.has_power(PowerUpType.SHIELD):
            # Shield effect
            shield_radius = self.size * 0.8 + math.sin(self.pulse) * 3
            pygame.draw.circle(player_surface, Colors.SHIELD, (self.size // 2, self.size // 2), shield_radius)
        
        # Player shape with animation
        pulse_size = 1 + math.sin(self.pulse) * 0.05  # Subtle pulsing effect
        points = []
        for i in range(5):  # Star shape
            angle_rad = math.radians(self.angle + i * 72)
            radius = self.size // 2 * pulse_size
            points.append((
                self.size // 2 + math.cos(angle_rad) * radius,
                self.size // 2 + math.sin(angle_rad) * radius
            ))
            angle_rad = math.radians(self.angle + i * 72 + 36)
            inner_radius = self.size // 4 * pulse_size
            points.append((
                self.size // 2 + math.cos(angle_rad) * inner_radius,
                self.size // 2 + math.sin(angle_rad) * inner_radius
            ))
        
        # Draw the star shape
        color = Colors.CORAL
        if self.has_power(PowerUpType.SLOW_TIME):
            color = Colors.LIGHT_BLUE
        elif self.has_power(PowerUpType.MAGNET):
            color = Colors.PURPLE
        
        pygame.draw.polygon(player_surface, color, points)
        
        # Draw a smaller circle in the center
        pygame.draw.circle(player_surface, Colors.OFF_WHITE, (self.size // 2, self.size // 2), self.size // 6)
        
        # Blit the player to the screen
        screen.blit(player_surface, (self.pos[0], self.pos[1]))


class Block:
    def __init__(self, block_type=None):
        self.size = Config.BLOCK_SIZE
        self.block_type = block_type if block_type else self._random_type()
        self.particles = []
        self.angle = random.randint(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        self.pulse = random.uniform(0, 2 * math.pi)
        self.power_up_type = None
        
        if self.block_type == BlockType.POWER_UP:
            self.power_up_type = random.choice(list(PowerUpType))
        
        self.reset()

    def _random_type(self):
        # Determine block type based on probabilities
        if random.random() < Config.POWER_UP_CHANCE:
            return BlockType.POWER_UP
        
        r = random.random()
        if r < 0.7:  # 70% chance of normal block
            return BlockType.NORMAL
        elif r < 0.85:  # 15% chance of harmful block
            return BlockType.HARMFUL
        else:  # 15% chance of bonus block
            return BlockType.BONUS

    def reset(self):
        self.pos = [random.randint(0, Config.WIDTH - self.size), -self.size]
        self.particles.clear()
        self.active = True
        self.scale = 1.0  # For appearing/disappearing animation

    def update(self, speed):
        if not self.active:
            self.scale -= 0.1
            if self.scale <= 0:
                self.scale = 0
            return
            
        self.pos[1] += speed
        self.angle = (self.angle + self.rotation_speed) % 360
        self.pulse = (self.pulse + Config.ANIMATION_SPEED) % (2 * math.pi)
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        
        # Add particles based on block type
        if random.random() < 0.1:
            if self.block_type == BlockType.HARMFUL:
                color = Colors.RED
            elif self.block_type == BlockType.BONUS:
                color = Colors.GREEN
            elif self.block_type == BlockType.POWER_UP:
                color = Colors.GOLD
            else:
                color = Colors.TEAL
                
            self.particles.append(
                Particle(
                    self.pos[0] + self.size // 2,
                    self.pos[1] + self.size,
                    color,
                    random.uniform(-1, 1),
                    random.uniform(1, 3),
                    random.randint(2, 5)
                )
            )

    def is_off_screen(self):
        return self.pos[1] >= Config.HEIGHT

    def deactivate(self):
        self.active = False
        # Create explosion particles
        count = 20 if self.block_type == BlockType.POWER_UP else 10
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            
            if self.block_type == BlockType.HARMFUL:
                color = Colors.RED
            elif self.block_type == BlockType.BONUS:
                color = Colors.GREEN
            elif self.block_type == BlockType.POWER_UP:
                color = Colors.GOLD
            else:
                color = Colors.TEAL
                
            self.particles.append(
                Particle(
                    self.pos[0] + self.size // 2,
                    self.pos[1] + self.size // 2,
                    color,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.randint(3, 8),
                    random.randint(20, 40)
                )
            )

    def draw(self, screen):
        # Draw particles
        for particle in self.particles:
            particle.draw(screen)
            
        if self.scale <= 0:
            return
            
        # Draw block with animation
        block_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Determine block shape and color based on type
        if self.block_type == BlockType.NORMAL:
            color = Colors.TEAL
            # Simple square with slight pulsing
            size = int(self.size * self.scale * (0.9 + 0.1 * math.sin(self.pulse)))
            pygame.draw.rect(
                block_surface, 
                color, 
                (self.size // 2 - size // 2, self.size // 2 - size // 2, size, size)
            )
            
        elif self.block_type == BlockType.HARMFUL:
            color = Colors.RED
            # Spiky shape
            points = []
            num_points = 8
            for i in range(num_points * 2):
                angle = math.radians(self.angle + i * 180 / num_points)
                radius = self.size // 2 * self.scale if i % 2 == 0 else self.size // 3 * self.scale
                points.append((
                    self.size // 2 + math.cos(angle) * radius,
                    self.size // 2 + math.sin(angle) * radius
                ))
            pygame.draw.polygon(block_surface, color, points)
            
        elif self.block_type == BlockType.BONUS:
            color = Colors.GREEN
            # Diamond shape
            size = int(self.size * self.scale * (0.9 + 0.1 * math.sin(self.pulse)))
            pygame.draw.polygon(
                block_surface,
                color,
                [
                    (self.size // 2, self.size // 2 - size // 2),
                    (self.size // 2 + size // 2, self.size // 2),
                    (self.size // 2, self.size // 2 + size // 2),
                    (self.size // 2 - size // 2, self.size // 2)
                ]
            )
            
        elif self.block_type == BlockType.POWER_UP:
            # Circle with glowing effect
            pulse_radius = self.size // 2 * self.scale * (0.9 + 0.1 * math.sin(self.pulse))
            
            # Outer glow
            for r in range(3):
                alpha = 150 - r * 50
                pygame.draw.circle(
                    block_surface, 
                    (255, 255, 200, alpha), 
                    (self.size // 2, self.size // 2), 
                    pulse_radius + r * 2
                )
            
            if self.power_up_type == PowerUpType.SHIELD:
                color = Colors.LIGHT_BLUE
                icon = "S"
            elif self.power_up_type == PowerUpType.SLOW_TIME:
                color = Colors.PURPLE
                icon = "T"
            elif self.power_up_type == PowerUpType.MAGNET:
                color = Colors.MINT
                icon = "M"
            elif self.power_up_type == PowerUpType.EXTRA_LIFE:
                color = Colors.CORAL
                icon = "♥"
                
            pygame.draw.circle(block_surface, Colors.GOLD, (self.size // 2, self.size // 2), pulse_radius)
            pygame.draw.circle(block_surface, Colors.OFF_WHITE, (self.size // 2, self.size // 2), pulse_radius * 0.7)
            
            # Draw power-up icon
            font = pygame.font.SysFont("arial", int(self.size // 2 * self.scale))
            text = font.render(icon, True, color)
            text_rect = text.get_rect(center=(self.size // 2, self.size // 2))
            block_surface.blit(text, text_rect)
            
        # Apply rotation if needed
        if self.rotation_speed != 0 and self.block_type != BlockType.POWER_UP:
            block_surface = pygame.transform.rotate(block_surface, self.angle)
            
        # Blit the block to the screen
        screen.blit(block_surface, (
            self.pos[0] + (self.size - block_surface.get_width()) // 2,
            self.pos[1] + (self.size - block_surface.get_height()) // 2
        ))


class SoundEffects:
    @staticmethod
    def generate_sounds():
        # Create dummy sounds
        sounds = {
            "collision": DummySound(),
            "powerup": DummySound(),
            "game_over": DummySound(),
            "score": DummySound(),
            "menu": DummySound()
        }
        return sounds


class DummySound:
    def __init__(self):
        pass
        
    def play(self):
        pass
        
    def set_volume(self, volume):
        pass


class Game:
    def __init__(self):
        pygame.init()
        
        # For web compatibility, use resizable mode
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Falling Blocks - Enhanced")
        self.clock = pygame.time.Clock()
        
        # Better fonts
        pygame.font.init()
        default_font = pygame.font.get_default_font()
        self.font = pygame.font.Font(default_font, 35)
        self.big_font = pygame.font.Font(default_font, 70)
        self.small_font = pygame.font.Font(default_font, 20)
        
        # Initialize game components
        self.init_game()
    
    def init_game(self):
        self.player = Player()
        self.blocks = []
        self.particles = []
        self.sounds = SoundEffects.generate_sounds()
        self.high_scores = [0] * Config.HIGH_SCORES_COUNT
        self.load_high_scores()
        self.menu_offset = 0
        self.shake_amount = 0
        self.slow_mo_factor = 1.0
        self.magnet_enabled = False
        
        # Background stars
        self.stars = []
        for _ in range(100):
            self.stars.append([
                random.randint(0, Config.WIDTH),
                random.randint(0, Config.HEIGHT),
                random.uniform(0.2, 1.0),
                random.choice([Colors.OFF_WHITE, Colors.LIGHT_BLUE, Colors.MINT])
            ])
        
        self.reset_game()
        self.state = GameState.MENU

    def load_high_scores(self):
        try:
            with open("high_scores.txt", "r") as f:
                self.high_scores = [int(score) for score in f.read().split(",")]
                # Ensure we have the right number of high scores
                while len(self.high_scores) < Config.HIGH_SCORES_COUNT:
                    self.high_scores.append(0)
        except:
            self.high_scores = [0] * Config.HIGH_SCORES_COUNT

    def save_high_scores(self):
        try:
            with open("high_scores.txt", "w") as f:
                f.write(",".join(map(str, self.high_scores)))
        except:
            pass  # Silently fail if we can't save

    def reset_game(self):
        self.player.reset_position()
        self.blocks.clear()
        self.particles.clear()
        self.score = 0
        self.speed = Config.INITIAL_SPEED
        self.lives = Config.LIVES
        self.magnet_enabled = False
        self.slow_mo_factor = 1.0
        self.shake_amount = 0

    def check_high_score(self):
        for i, score in enumerate(self.high_scores):
            if self.score > score:
                # Insert new high score
                self.high_scores.insert(i, self.score)
                self.high_scores.pop()  # Remove lowest score
                self.save_high_scores()
                return True
        return False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                width = max(event.w, Config.MIN_WIDTH)  # Minimum width
                height = max(event.h, Config.MIN_HEIGHT)  # Minimum height
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                # Update game dimensions
                scale_x = width / Config.WIDTH
                scale_y = height / Config.HEIGHT
                Config.WIDTH = width
                Config.HEIGHT = height
                # Update player position
                self.player.pos[0] *= scale_x
                self.player.pos[1] = Config.HEIGHT - 2 * self.player.size

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
                elif self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_h:
                        self.state = GameState.HIGH_SCORES
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_h:
                        self.state = GameState.HIGH_SCORES
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p or event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                elif self.state == GameState.HIGH_SCORES:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU

            if event.type == pygame.KEYUP:
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.player.stop()

            # Add touch controls for mobile web
            if event.type == pygame.FINGERDOWN:
                if self.state == GameState.PLAYING:
                    if event.x < 0.5:
                        self.player.move(-1)
                    else:
                        self.player.move(1)
                elif self.state in [GameState.MENU, GameState.GAME_OVER, GameState.PAUSED]:
                    self.state = GameState.PLAYING
                    if self.state == GameState.GAME_OVER:
                        self.reset_game()
                elif self.state == GameState.HIGH_SCORES:
                    self.state = GameState.MENU

            if event.type == pygame.FINGERUP:
                if self.state == GameState.PLAYING:
                    self.player.stop()

        return True

    def update(self):
        # Update menu animation
        self.menu_offset = (self.menu_offset + 1) % 360
        
        # Update screen shake
        if self.shake_amount > 0:
            self.shake_amount *= 0.9
            if self.shake_amount < 0.1:
                self.shake_amount = 0
        
        # Update stars
        for star in self.stars:
            star[1] += star[2] * 0.5  # Move stars based on size
            if star[1] > Config.HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, Config.WIDTH)
        
        if self.state != GameState.PLAYING:
            return

        # Check player power-ups
        self.slow_mo_factor = 0.5 if self.player.has_power(PowerUpType.SLOW_TIME) else 1.0
        self.magnet_enabled = self.player.has_power(PowerUpType.MAGNET)
        
        self.player.update()
        
        # Update global particles
        self.particles = [p for p in self.particles if p.update()]

        # Spawn new blocks
        if len(self.blocks) < Config.MAX_BLOCKS and random.random() < Config.BLOCK_SPAWN_RATE * self.slow_mo_factor:
            self.blocks.append(Block())

        # Update blocks and check for scoring
        for block in self.blocks[:]:
            current_speed = self.speed * self.slow_mo_factor
            
            # Apply magnet effect if active
            if self.magnet_enabled and block.block_type in [BlockType.BONUS, BlockType.POWER_UP]:
                # Calculate vector from block to player
                dx = (self.player.pos[0] + self.player.size // 2) - (block.pos[0] + block.size // 2)
                dy = (self.player.pos[1] + self.player.size // 2) - (block.pos[1] + block.size // 2)
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < Config.MAGNET_RADIUS:
                    # Normalize and apply attraction
                    attraction = 5 * (1 - distance / Config.MAGNET_RADIUS)
                    if distance > 0:
                        block.pos[0] += dx / distance * attraction
                        block.pos[1] += dy / distance * attraction
            
            block.update(current_speed)
            
            # Check if block is off screen
            if block.is_off_screen():
                # Score points for letting harmful blocks pass
                if block.block_type == BlockType.HARMFUL and block.active:
                    self.score += 2
                    
                    # Add score particles
                    for _ in range(5):
                        self.particles.append(
                            Particle(
                                block.pos[0] + block.size // 2,
                                Config.HEIGHT,
                                Colors.GOLD,
                                random.uniform(-2, 2),
                                random.uniform(-5, -2),
                                random.randint(3, 6)
                            )
                        )
                
                # Only remove blocks that aren't showing destruction animation
                if not block.particles:
                    self.blocks.remove(block)

        # Check for collisions with player
        player_rect = pygame.Rect(self.player.pos[0], self.player.pos[1], self.player.size, self.player.size)
        for block in self.blocks[:]:
            if not block.active or block.scale <= 0:
                continue
                
            block_rect = pygame.Rect(block.pos[0], block.pos[1], block.size, block.size)
            if player_rect.colliderect(block_rect):
                block.deactivate()
                
                if block.block_type == BlockType.HARMFUL:
                    if not self.player.has_power(PowerUpType.SHIELD):
                        self.lives -= 1
                        self.shake_amount = 10
                        
                        if self.lives == 0:
                            if self.check_high_score():
                                self.state = GameState.HIGH_SCORES
                            else:
                                self.state = GameState.GAME_OVER
                    else:
                        # Shield absorbed the hit
                        pass
                        
                elif block.block_type == BlockType.NORMAL:
                    self.score += 1
                
                elif block.block_type == BlockType.BONUS:
                    self.score += 5
                    
                elif block.block_type == BlockType.POWER_UP:
                    if block.power_up_type == PowerUpType.SHIELD:
                        self.player.activate_power(PowerUpType.SHIELD, Config.SHIELD_DURATION)
                    elif block.power_up_type == PowerUpType.SLOW_TIME:
                        self.player.activate_power(PowerUpType.SLOW_TIME, Config.SLOW_TIME_DURATION)
                    elif block.power_up_type == PowerUpType.MAGNET:
                        self.player.activate_power(PowerUpType.MAGNET, Config.MAGNET_DURATION)
                    elif block.power_up_type == PowerUpType.EXTRA_LIFE:
                        self.lives = min(self.lives + 1, 5)  # Cap at 5 lives
                
                # Only remove blocks that aren't showing destruction animation
                if not block.particles:
                    self.blocks.remove(block)

        # Update speed based on score, but cap it
        self.speed = min(Config.INITIAL_SPEED + (self.score // 15), 15)

    def draw(self):
        self.screen.fill(Colors.BACKGROUND)
        
        # Draw stars in background
        for star in self.stars:
            # Make stars twinkle
            brightness = 0.5 + 0.5 * math.sin(self.menu_offset * 0.01 + star[0] * 0.01)
            color = tuple(int(c * brightness) for c in star[3][:3])
            pygame.draw.circle(self.screen, color, (star[0], star[1]), star[2])
        
        # Apply screen shake if active
        shake_offset = [0, 0]
        if self.shake_amount > 0:
            shake_offset = [
                random.randint(-int(self.shake_amount), int(self.shake_amount)),
                random.randint(-int(self.shake_amount), int(self.shake_amount))
            ]
        
        if self.state == GameState.MENU:
            # Animated title
            title_y = Config.HEIGHT // 6 + math.sin(self.menu_offset * 0.05) * 10
            self.draw_text("FALLING BLOCKS", self.big_font, Colors.MUSTARD, Config.WIDTH // 2, title_y)
            
            # Menu options with pulsing effect
            pulse = 0.7 + 0.3 * math.sin(self.menu_offset * 0.1)
            option_color = tuple(int(c * pulse) for c in Colors.OFF_WHITE)
            
            self.draw_text("Press SPACE to start", self.font, option_color, Config.WIDTH // 2, Config.HEIGHT // 6 + 80)
            self.draw_text("Press H for high scores", self.font, option_color, Config.WIDTH // 2, Config.HEIGHT // 6 + 130)
            
            # Game instructions
            help_y = Config.HEIGHT // 2 + 50  # Moved down to avoid overlap
            help_bg = pygame.Surface((Config.WIDTH - 200, 300), pygame.SRCALPHA)  # Made taller
            help_bg.fill((0, 0, 0, 180))  # Made more opaque
            self.screen.blit(help_bg, (100, help_y - 20))
            
            self.draw_text("HOW TO PLAY", self.font, Colors.MINT, Config.WIDTH // 2, help_y)
            
            # Draw block examples and their explanations
            block_x = Config.WIDTH // 4
            text_x = block_x + 180
            spacing = 50  # Increased spacing
            
            # Normal block
            block = Block(BlockType.NORMAL)
            block.pos = [block_x - block.size // 2, help_y + spacing]
            block.draw(self.screen)
            self.draw_text("Normal Block (+1 point)", self.small_font, Colors.TEAL, text_x, help_y + spacing + 10)
            
            # Harmful block
            block = Block(BlockType.HARMFUL)
            block.pos = [block_x - block.size // 2, help_y + spacing * 2]
            block.draw(self.screen)
            self.draw_text("Harmful Block (avoid or +2 points if dodged)", self.small_font, Colors.RED, text_x, help_y + spacing * 2 + 10)
            
            # Bonus block
            block = Block(BlockType.BONUS)
            block.pos = [block_x - block.size // 2, help_y + spacing * 3]
            block.draw(self.screen)
            self.draw_text("Bonus Block (+5 points)", self.small_font, Colors.GREEN, text_x, help_y + spacing * 3 + 10)
            
            # Power-up blocks
            power_up_x = Config.WIDTH * 3 // 4 - 50
            power_text_x = power_up_x + 180
            
            # Shield power-up
            block = Block(BlockType.POWER_UP)
            block.power_up_type = PowerUpType.SHIELD
            block.pos = [power_up_x - block.size // 2, help_y + spacing]
            block.draw(self.screen)
            self.draw_text("Shield (blocks damage)", self.small_font, Colors.LIGHT_BLUE, power_text_x, help_y + spacing + 10)
            
            # Slow time power-up
            block = Block(BlockType.POWER_UP)
            block.power_up_type = PowerUpType.SLOW_TIME
            block.pos = [power_up_x - block.size // 2, help_y + spacing * 2]
            block.draw(self.screen)
            self.draw_text("Slow Time (reduces block speed)", self.small_font, Colors.PURPLE, power_text_x, help_y + spacing * 2 + 10)
            
            # Magnet power-up
            block = Block(BlockType.POWER_UP)
            block.power_up_type = PowerUpType.MAGNET
            block.pos = [power_up_x - block.size // 2, help_y + spacing * 3]
            block.draw(self.screen)
            self.draw_text("Magnet (attracts bonus items)", self.small_font, Colors.MINT, power_text_x, help_y + spacing * 3 + 10)
            
            # Controls
            controls_y = help_y + spacing * 4 + 30  # Increased spacing
            controls_bg = pygame.Surface((Config.WIDTH - 200, 50), pygame.SRCALPHA)
            controls_bg.fill((0, 0, 0, 180))  # Made more opaque
            self.screen.blit(controls_bg, (100, controls_y - 10))
            
            self.draw_text("Controls: ← → arrows to move   |   P to pause   |   ESC for menu", 
                         self.small_font, Colors.OFF_WHITE, Config.WIDTH // 2, controls_y)
            
            # Draw animated blocks falling in background
            if random.random() < 0.02:
                block = Block()
                block.pos = [random.randint(0, Config.WIDTH - block.size), -block.size]
                self.blocks.append(block)
            
            for block in self.blocks[:]:
                block.update(2)
                block.draw(self.screen)
                if block.pos[1] > Config.HEIGHT:
                    self.blocks.remove(block)
                    
        elif self.state == GameState.HIGH_SCORES:
            self.draw_text("HIGH SCORES", self.big_font, Colors.GOLD, Config.WIDTH // 2, Config.HEIGHT // 4)
            
            for i, score in enumerate(self.high_scores):
                if score == 0:
                    continue
                    
                y_pos = Config.HEIGHT // 3 + 60 * i
                rank_color = Colors.GOLD if i == 0 else Colors.OFF_WHITE
                
                self.draw_text(f"{i+1}. {score}", self.font, rank_color, Config.WIDTH // 2, y_pos)
            
            pulse = 0.7 + 0.3 * math.sin(self.menu_offset * 0.1)
            option_color = tuple(int(c * pulse) for c in Colors.OFF_WHITE)
            self.draw_text("Press SPACE to return", self.font, option_color, Config.WIDTH // 2, Config.HEIGHT * 3 // 4)
            
        elif self.state == GameState.GAME_OVER:
            self.draw_text("GAME OVER", self.big_font, Colors.CORAL, Config.WIDTH // 2, Config.HEIGHT // 3)
            self.draw_text(f"Final Score: {self.score}", self.font, Colors.OFF_WHITE, Config.WIDTH // 2,
                           Config.HEIGHT // 2)
            
            pulse = 0.7 + 0.3 * math.sin(self.menu_offset * 0.1)
            option_color = tuple(int(c * pulse) for c in Colors.OFF_WHITE)
            
            self.draw_text("Press SPACE to restart", self.font, option_color, Config.WIDTH // 2,
                           Config.HEIGHT * 2 // 3)
            self.draw_text("Press H for high scores", self.font, option_color, Config.WIDTH // 2,
                           Config.HEIGHT * 2 // 3 + 60)
                           
        elif self.state == GameState.PAUSED:
            # Semi-transparent overlay
            overlay = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            self.draw_text("PAUSED", self.big_font, Colors.MUSTARD, Config.WIDTH // 2, Config.HEIGHT // 3)
            
            pulse = 0.7 + 0.3 * math.sin(self.menu_offset * 0.1)
            option_color = tuple(int(c * pulse) for c in Colors.OFF_WHITE)
            
            self.draw_text("Press P to resume", self.font, option_color, Config.WIDTH // 2, Config.HEIGHT // 2)
            self.draw_text("Press ESC for menu", self.font, option_color, Config.WIDTH // 2, Config.HEIGHT // 2 + 60)

        if self.state in (GameState.PLAYING, GameState.PAUSED):
            # Draw global particles
            for particle in self.particles:
                particle.draw(self.screen)
            
            # Create a temporary surface for applying screen shake
            if self.shake_amount > 0:
                temp_surface = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
                
                # Draw player and blocks to the temporary surface
                self.player.draw(temp_surface)
                for block in self.blocks:
                    block.draw(temp_surface)
                
                # Blit with shake offset
                self.screen.blit(temp_surface, shake_offset)
            else:
                # Draw directly to screen if no shake
                self.player.draw(self.screen)
                for block in self.blocks:
                    block.draw(self.screen)
            
            # Draw HUD
            score_text = f"Score: {self.score}"
            level_text = f"Level: {min(10, self.speed - 4)}"
            
            # Draw lives as hearts
            heart_spacing = 40
            heart_y = 30
            for i in range(self.lives):
                heart_x = Config.WIDTH - 50 - i * heart_spacing
                
                # Draw heart shape
                heart_color = Colors.CORAL
                if i == 0:  # Make the last heart pulse
                    pulse = 0.8 + 0.2 * math.sin(self.menu_offset * 0.1)
                    heart_color = tuple(int(c * pulse) for c in heart_color)
                
                # Draw a simple heart shape
                heart_size = 15
                pygame.draw.polygon(self.screen, heart_color, [
                    (heart_x, heart_y + heart_size // 2),
                    (heart_x - heart_size // 2, heart_y),
                    (heart_x - heart_size, heart_y + heart_size // 2),
                    (heart_x - heart_size // 2, heart_y + heart_size),
                ])
                pygame.draw.polygon(self.screen, heart_color, [
                    (heart_x, heart_y + heart_size // 2),
                    (heart_x + heart_size // 2, heart_y),
                    (heart_x + heart_size, heart_y + heart_size // 2),
                    (heart_x + heart_size // 2, heart_y + heart_size),
                ])
            
            # HUD Background
            hud_bg = pygame.Surface((200, 90), pygame.SRCALPHA)
            hud_bg.fill((0, 0, 0, 128))
            self.screen.blit(hud_bg, (Config.WIDTH - 220, 70))
            
            self.draw_text(score_text, self.font, Colors.MUSTARD, Config.WIDTH - 120, 80)
            self.draw_text(level_text, self.font, Colors.MINT, Config.WIDTH - 120, 120)
            
            # Show active power-ups
            power_up_x = 20
            power_up_y = 20
            power_text = ""
            
            if self.player.has_power(PowerUpType.SHIELD):
                power_text += "SHIELD "
                remaining = self.player.active_powers[PowerUpType.SHIELD] // Config.FPS
                power_text += f"{remaining}s "
            
            if self.player.has_power(PowerUpType.SLOW_TIME):
                power_text += "SLOW "
                remaining = self.player.active_powers[PowerUpType.SLOW_TIME] // Config.FPS
                power_text += f"{remaining}s "
            
            if self.player.has_power(PowerUpType.MAGNET):
                power_text += "MAGNET "
                remaining = self.player.active_powers[PowerUpType.MAGNET] // Config.FPS
                power_text += f"{remaining}s "
            
            if power_text:
                power_bg = pygame.Surface((len(power_text) * 10 + 20, 30), pygame.SRCALPHA)
                power_bg.fill((0, 0, 0, 128))
                self.screen.blit(power_bg, (power_up_x - 10, power_up_y - 5))
                self.draw_text(power_text, self.small_font, Colors.LIGHT_BLUE, power_up_x + len(power_text) * 5, power_up_y)

        pygame.display.flip()

    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.centerx = x
        text_rect.y = y
        self.screen.blit(text_surface, text_rect)

    async def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)
            await asyncio.sleep(0)  # Required for web compatibility

        pygame.quit()


async def main():
    game = Game()
    try:
        await game.run()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())

# For web platform
if __name__ == "__main__" and hasattr(sys, "__EMSCRIPTEN__"):
    asyncio.create_task(main())
    asyncio.get_event_loop().run_forever()