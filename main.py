# Jumpy! (a platform game)
# Art from Kenney.nl
# surfside by https://opengameart.org/users/axtoncrolley
# jump-and-run-tropical-mix by https://opengameart.org/users/bart

import pygame as pg
import random
from settings import *
from sprites import *
from os import path


class Game:
    def __init__(self):
        # initialize game window, etc
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.font_name = pg.font.match_font(FONT_NAME)
        self.load_data()

    def load_data(self):
        self.dir = path.dirname(__file__)
        img_dir = path.join(self.dir, 'img')

        # load high score
        with open(path.join(self.dir, HS_FILE), 'r+') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

        # load spritesheet image
        self.spritesheet = Spritesheet(path.join(img_dir, SPRITESHEET))

        # cloud images
        self.cloud_images = []
        for i in range(1, 4):
            self.cloud_images.append(pg.image.load(path.join(img_dir, 'cloud{}.png'.format(i))).convert())

        # load sounds
        self.snd_dir = path.join(self.dir, 'snd')
        self.jump_sound = pg.mixer.Sound(path.join(self.snd_dir, 'jump.wav'))
        self.boost_sound = pg.mixer.Sound(path.join(self.snd_dir, 'boost.wav'))    


    def new(self):
        # start a new game
        self.score = 0
        self.all_sprites = pg.sprite.pygame.sprite.LayeredUpdates()
        self.platforms = pg.sprite.Group()
        self.powerups = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.clouds = pg.sprite.Group()
        self.player = Player(self)
        for plat in PLATFORM_LIST:
            Platform(self, *plat)
        self.mob_timer = 0
        pg.mixer.music.load(path.join(self.snd_dir, 'game_music.ogg'))
        for i in range(8):
            c = Cloud(self)
            c.rect.y += 500
        self.run()
 
    
    def run(self):
        # game loop
        pg.mixer.music.play(loops=-1)
        self.playing = True
        while self.playing:
              self.clock.tick(FPS)
              self.events()
              self.update()
              self.draw()
        pg.mixer.music.fadeout(500)    
        
    def update(self):
        # game loop - update
        self.all_sprites.update()
        # spawn a mob?
        now = pg.time.get_ticks()
        if now - self.mob_timer > 5000 + random.choice([-1000, -500, 0, 500, 1000]):
            self.mob_timer = now
            Mob(self)
        # hit mobs?
        mob_hits = pg.sprite.spritecollide(self.player, self.mobs, False, pg.sprite.collide_mask)
        if mob_hits:
            self.playing = False

        # check if player hits a platfirn - only if falling
        if self.player.vel.y > 0: 
            hits = pg.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                if self.player.pos.x < lowest.rect.right + 10 and \
                    self.player.pos.x > lowest.rect.left + 10:  
                     if self.player.pos.y < lowest.rect.centery:
                        self.player.pos.y = lowest.rect.top
                        self.player.vel.y = 0
                        self.player.jumping = False

        # if player reaches top 1/4 of the screen
        if self.player.rect.top <= HEIGHT / 4:
            if random.randrange(100) < 15:
                Cloud(self)
            self.player.pos.y += max(abs(self.player.vel.y), 2)
            for cloud in self.clouds:
                cloud.rect.y += max(abs(self.player.vel.y / 2), 2)
            for mob in self.mobs:
                mob.rect.y += max(abs(self.player.vel.y), 2)
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.vel.y), 2)
                if plat.rect.top >= HEIGHT:
                    plat.kill()
                    self.score += 10

        # if player hits powerup
        pow_hits = pg.sprite.spritecollide(self.player, self.powerups, True)
        for pow in pow_hits:
            if pow.type == 'boost':
                self.boost_sound.play()
                self.player.vel.y = -BOOST_POWER
                self.player.jumping = False

        # die!
        if self.player.rect.bottom > HEIGHT:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()
            if len(self.platforms) == 0:
                self.playing = False

        # spawn new platforms to keep same average number
        while len(self.platforms) < 6:
            width = random.randrange(50, 100)
            Platform(self, random.randrange(0, WIDTH-width),
                    random.randrange(-75, -30))

    def events(self):
        # game loop - events
        for event in pg.event.get():
            # check for closing the window
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key  == pg.K_SPACE:
                    self.player.jump()
            if event.type == pg.KEYUP:
                if event.key  == pg.K_SPACE:
                    self.player.jump_cut()
            
    
    def draw(self):
        # game loop - draw
        self.screen.fill(BGCOLOR)
        self.all_sprites.draw(self.screen)
        self.draw_text(str(self.score), 22, WHITE, WIDTH / 2, 15)
        # *after* drawing everything, flip the display
        pg.display.flip()


    def show_start_screen(self):
        # game splash/start screen
        pg.mixer.music.load(path.join(self.snd_dir, 'menu_music.ogg'))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(BLACK)
        self.draw_text(TITLE, 70, LIGHTBLUE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Arrows or A and D to move, Space to jump", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("PRESS ANY KEY TO PLAY", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 5)
        self.draw_text("High score: " + str(self.highscore), 22, WHITE, WIDTH / 2, 15)
        pg.display.flip()
        self.wait_for_key()
        pg.mixer.music.fadeout(500)


    def show_go_screen(self):
        # game over/continue
        if not self.running:
            return
        pg.mixer.music.load(path.join(self.snd_dir, 'menu_music.ogg'))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(BLACK)
        self.draw_text("GAME OVER", 70, RED, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Score: " + str(self.score), 30, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("PRESS ANY KEY TO PLAY AGAIN", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 5 + 60)
        if self.score > self.highscore:
            self.highscore = self.score
            self.draw_text("NEW HIGH SCORE!", 30, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
            with open(path.join(self.dir, HS_FILE), 'w') as f:
                f.write(str(self.score))
        else:
            self.draw_text("High score: " + str(self.highscore), 30, WHITE, WIDTH / 2, HEIGHT / 2 + 40)    
        pg.display.flip()
        self.wait_for_key()
        pg.mixer.music.fadeout(500)


    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pg.KEYUP:
                    waiting = False
       
    
    def draw_text(self, text, size, color, x, y):
        font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)


g = Game()
g.show_start_screen()
while g.running:
    g.new()
    g.show_go_screen()


pg.quit()
    

    
    
