from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
import os
import time
import random
pygame.init()
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders by Alex")

# Navele inamice
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

# Nava jucatorului
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

# Laserele
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# Background-ul
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))
IC = pygame.image.load(os.path.join("assets", "gameIc.jpg"))

# Sounds
pygame.mixer.music.load('sounds/soundtrack.mp3')
pygame.mixer.music.play(-1)

pygame.display.set_icon(IC)

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        value = 0
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        explosion = pygame.mixer.Sound('sounds/explosion.wav')
                        explosion.play()
                        if obj.laser_img == BLUE_LASER:
                            value += 30
                        elif obj.laser_img == GREEN_LASER:
                            value += 60
                        else:
                            value += 100
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)
        return value

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (self.x, self.y +
            self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + 
            self.ship_img.get_height() + 10, self.ship_img.get_width() * 
            (self.health/self.max_health), 10))


class Enemy(Ship):
    COLOR_MAP = {
                "red": (RED_SPACE_SHIP, RED_LASER),
                "green": (GREEN_SPACE_SHIP, GREEN_LASER),
                "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
                }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x-20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def InsertNewHigh(value):
    F = open("highScore.txt", "r+")
    F.seek(0)
    F.truncate()
    F.write(str(value))
    F.close()

def main():
    run = True
    FPS = 60
    level = 0
    lives = 5
    Score = 0
    lost_font = pygame.font.SysFont("comicsans", 60)
    main_font = pygame.font.SysFont("comicsans", 40)

    enemies = []
    wave_length = 5
    enemy_vel = 1

    player_vel = 5
    laser_vel = 5

    player = Player(300, 630)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0


    def redraw_window():
        WIN.blit(BG, (0,0))
        currentScore = str(Score)
        F = open("highScore.txt", "r+")
        high = F.read()
        F.close
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))
        score_label = main_font.render(f"Score:{currentScore} High Score:{high}", 1, (255, 255, 255))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(score_label, (WIDTH/2 - score_label.get_width()/2, 10))
        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            gameovr = pygame.mixer.Sound('sounds/game_over.wav')
            gameovr.play()
            lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        if Score != 0 and Score > int(high):
            InsertNewHigh(Score)
        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 2:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            Score += (level - 1) * 100
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - player_vel > 0: # left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH: # right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0: # up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT: # down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
            shoot = pygame.mixer.Sound('sounds/shoot.wav')
            shoot.play()
        if keys[pygame.K_ESCAPE]:
            InsertNewHigh(Score)
            run = False

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        Score += player.move_lasers(-laser_vel, enemies)

def helpMe():
    run = True
    small_font = pygame.font.SysFont("comicsans", 30)
    while run:
        WIN.blit(BG, (0,0))
        title_label = small_font.render("CONTROLS LIST:", 1, (255, 255, 255))
        up_label = small_font.render("'w' - up", 1, (255, 255, 255))
        down_label = small_font.render("'s' - down", 1, (255, 255, 255))
        left_label = small_font.render("'a' - left", 1, (255, 255, 255))
        right_label = small_font.render("'d' - right", 1, (255, 255, 255))
        esc_label = small_font.render("'esc' - going to main menu", 1, (255, 255, 255))
        space_label = small_font.render("'space' - shoot", 1, (255, 255, 255))
        red_label = small_font.render(" - 100 points", 1, (255, 255, 255))
        green_label = small_font.render(" - 60 points", 1, (255, 255, 255))
        blue_label = small_font.render(" - 30 points", 1, (255, 255, 255))
        points_label = small_font.render("POINTS LIST:", 1, (255, 255, 255))

        currentY = 200
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, currentY))
        currentY+=title_label.get_height() + 12
        WIN.blit(up_label, (WIDTH/2 - up_label.get_width()/2, currentY))
        currentY+=up_label.get_height()
        WIN.blit(down_label, (WIDTH/2 - down_label.get_width()/2, currentY))
        currentY += down_label.get_height()
        WIN.blit(left_label, (WIDTH/2 - left_label.get_width()/2, currentY))
        currentY +=left_label.get_height()
        WIN.blit(right_label, (WIDTH/2 - right_label.get_width()/2, currentY))
        currentY +=right_label.get_height()
        WIN.blit(esc_label, (WIDTH/2 - esc_label.get_width()/2, currentY))
        currentY += esc_label.get_height()
        WIN.blit(space_label, (WIDTH/2 - space_label.get_width()/2, currentY))
        currentY += space_label.get_height() + 12
        WIN.blit(points_label, (WIDTH/2 - points_label.get_width()/2, currentY))
        currentY += points_label.get_height() + 7
        WIN.blit(RED_SPACE_SHIP, (260, currentY))
        WIN.blit(red_label, (260 + RED_SPACE_SHIP.get_width() + 2, currentY + 10))
        currentY += RED_SPACE_SHIP.get_height()
        WIN.blit(GREEN_SPACE_SHIP, (263, currentY))
        WIN.blit(green_label, (263 + GREEN_SPACE_SHIP.get_width() + 2, currentY + 13))
        currentY += GREEN_SPACE_SHIP.get_height()
        WIN.blit(BLUE_SPACE_SHIP, (270, currentY))
        WIN.blit(blue_label, (270 + BLUE_SPACE_SHIP.get_width() + 13, currentY + 14))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

def main_menu():
    title_font = pygame.font.SysFont("comicsans", 70)
    medium_font = pygame.font.SysFont("comicsans", 50)
    small_font = pygame.font.SysFont("comicsans", 30)
    run = True
    while run:
        WIN.blit(BG, (0,0))
        F = open("highScore.txt", "r+")
        high = F.read()
        F.close()
        highScore = medium_font.render(f"High Score: {high}", 1, (255, 255, 255))
        title_label = title_font.render("Press 'k' key to start...", 1, (255,255,255))
        help_label = small_font.render("Press 'h' to access the help menu", 1, (255,255,255))
        exit_label = small_font.render("Press 'esc' to quit the game", 1, (255, 255, 255))
        reset_label = small_font.render("Press 'r' to reset your High Score", 1, (255, 255, 255))

        WIN.blit(highScore, (WIDTH/2 - highScore.get_width()/2, 350 - highScore.get_height()))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))
        WIN.blit(help_label, (WIDTH/2 - help_label.get_width()/2, 750 - help_label.get_height() - exit_label.get_height() - reset_label.get_height()))
        WIN.blit(exit_label, (WIDTH/2 - exit_label.get_width()/2, 750 - exit_label.get_height() - reset_label.get_height()))
        WIN.blit(reset_label, (WIDTH/2 - reset_label.get_width()/2, 750 - reset_label.get_height()))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_k:
                    main()
                elif event.key == pygame.K_h:
                    helpMe()
                elif event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_r:
                    F = open("highScore.txt", "r+")
                    F.seek(0)
                    F.truncate()
                    F.write("0")
                    F.close()
    pygame.quit()

main_menu()