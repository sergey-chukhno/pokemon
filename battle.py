import pygame
import random
import sys


pygame.init()


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

ELEMENT_ADVANTAGES = {
    'fire': {'plant': 2.0, 'water': 0.5, 'fire': 1.0},
    'water': {'fire': 2.0, 'plant': 0.5, 'water': 1.0},
    'plant': {'water': 2.0, 'fire': 0.5, 'plant': 1.0}
}

ELEMENT_COLORS = {
    'fire': (255, 69, 0),    
    'water': (0, 191, 255),  
    'plant': (34, 139, 34)  
}

class Pokemon:
    def __init__(self, name, x, y, element):
        self.name = name
        self.x = x
        self.y = y
        self.element = element
        self.color = ELEMENT_COLORS[element] 
        self.health = 100
        self.level = 1
        self.experience = 0
        self.exp_to_next_level = 100 
        self.radius = 30
        self.defense_active = False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        
        font = pygame.font.Font(None, 24)
        xp_label = font.render("XP", True, BLACK)
        screen.blit(xp_label, (self.x - 25, self.y - 115))
        
        exp_percent = self.experience / self.exp_to_next_level
        pygame.draw.rect(screen, BLACK, (self.x - 30, self.y - 100, 60, 10), 1)
        pygame.draw.rect(screen, GREEN, (self.x - 29, self.y - 99, int(58 * exp_percent), 8))
        
    
        health_label = font.render("Health", True, BLACK)
        screen.blit(health_label, (self.x - 25, self.y - 85))
        
        pygame.draw.rect(screen, BLACK, (self.x - 30, self.y - 50, 60, 10), 1)
        health_width = (self.health / 100) * 58
        pygame.draw.rect(screen, BLUE, (self.x - 29, self.y - 49, health_width, 8))
        
        health_text = font.render(f"{int(self.health)}/100", True, BLACK)
        screen.blit(health_text, (self.x - 25, self.y - 70))
        
        level_text = font.render(f"Lvl {self.level}", True, BLACK)
        screen.blit(level_text, (self.x - 20, self.y + 40))

    def gain_experience(self, amount):
        self.experience += amount
        if self.experience >= self.exp_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5) 
        self.health = 100 

    def attack(self, target):
        if not target.defense_active:
            base_damage = random.randint(10, 20) * (1 + self.level * 0.1) 
            multiplier = ELEMENT_ADVANTAGES[self.element][target.element]
            damage = int(base_damage * multiplier)
            target.health = max(0, target.health - damage)
            self.gain_experience(10)  
        else:
            base_damage = random.randint(5, 10) * (1 + self.level * 0.1)
            multiplier = ELEMENT_ADVANTAGES[self.element][target.element]
            damage = int(base_damage * multiplier)
            target.health = max(0, target.health - damage)
            target.defense_active = False
            self.gain_experience(10)

    def defense(self):
        self.defense_active = True

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pokemon Battle")
        self.clock = pygame.time.Clock()
        
        elements = ['fire', 'water', 'plant']
        player_element = random.choice(elements)
        enemy_element = random.choice(elements)
        
        self.player_pokemon = Pokemon("Player", 200, 400, player_element)
        self.enemy_pokemon = Pokemon("Enemy", 600, 200, enemy_element)
        
        # Players menu
        self.buttons = [
            {"text": "Attack", "rect": pygame.Rect(50, 500, 100, 40)},
            {"text": "Defense", "rect": pygame.Rect(200, 500, 100, 40)},
            {"text": "Catch", "rect": pygame.Rect(350, 500, 100, 40)}
        ]
        
        self.font = pygame.font.Font(None, 36)
        self.selected_button = 0 
        self.message = ""
        self.message_timer = 0
        self.message_duration = 80 
        self.message_font = pygame.font.Font(None, 48)  

    def draw_menu(self):
        for i, button in enumerate(self.buttons):
            color = BLUE if i == self.selected_button else (100, 100, 255)
            pygame.draw.rect(self.screen, color, button["rect"])
            text = self.font.render(button["text"], True, WHITE)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)

        player_info = f"Your {self.player_pokemon.element} Pokemon (Lvl {self.player_pokemon.level})"
        enemy_info = f"Enemy {self.enemy_pokemon.element} Pokemon (Lvl {self.enemy_pokemon.level})"
        
        player_text = self.font.render(player_info, True, BLACK)
        enemy_text = self.font.render(enemy_info, True, BLACK)
        self.screen.blit(player_text, (50, 50))
        self.screen.blit(enemy_text, (550, 50))

    def show_message(self, text):
        self.message = text
        self.message_timer = self.message_duration

    def draw_message(self):
        if self.message_timer > 0:
            message_text = self.message_font.render(self.message, True, BLACK)
            text_rect = message_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(message_text, text_rect)
            self.message_timer -= 1

    def enemy_turn(self):
        action = random.choice(["attack", "defense"])
        if action == "attack":
            self.enemy_pokemon.attack(self.player_pokemon)
            self.show_message(f"Enemy {self.enemy_pokemon.element} Pokemon attacks!")
        else:
            self.enemy_pokemon.defense()
            self.show_message(f"Enemy {self.enemy_pokemon.element} Pokemon defends!")

    def try_catch(self):
        if self.enemy_pokemon.health < 30:
            catch_chance = random.random()
            if catch_chance < 0.7:
                return True
        return False

    def check_game_over(self):
        if self.player_pokemon.health <= 0:
            self.show_message("Game Over - Enemy Wins!")
            pygame.time.wait(5000) 
            return True
        elif self.enemy_pokemon.health <= 0:
            self.show_message("Congratulations - You Win!")
            pygame.time.wait(5000) 
            return True
        return False

    def run(self):
        running = True
        player_turn = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN and player_turn:
                    if event.key == pygame.K_LEFT:
                        self.selected_button = (self.selected_button - 1) % len(self.buttons)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_button = (self.selected_button + 1) % len(self.buttons)
                    elif event.key == pygame.K_RETURN:
                        if self.selected_button == 0:
                            self.player_pokemon.attack(self.enemy_pokemon)
                            self.show_message(f"Your {self.player_pokemon.element} Pokemon attacks!")
                            player_turn = False
                        elif self.selected_button == 1:  
                            self.player_pokemon.defense()
                            self.show_message(f"Your {self.player_pokemon.element} Pokemon defends!")
                            player_turn = False
                        elif self.selected_button == 2: 
                            if self.try_catch():
                                self.show_message("Pokemon caught successfully!")
                                pygame.time.wait(3000)
                                running = False
                            else:
                                self.show_message("Catch failed!")
                                player_turn = False

                if event.type == pygame.MOUSEBUTTONDOWN and player_turn:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button["rect"].collidepoint(mouse_pos):
                            if i == 0: 
                                self.player_pokemon.attack(self.enemy_pokemon)
                                self.show_message(f"Your {self.player_pokemon.element} Pokemon attacks!")
                                player_turn = False
                            elif i == 1: 
                                self.player_pokemon.defense()
                                self.show_message(f"Your {self.player_pokemon.element} Pokemon defends!")
                                player_turn = False
                            elif i == 2: 
                                if self.try_catch():
                                    self.show_message("Pokemon caught successfully!")
                                    pygame.time.wait(3000)
                                    running = False
                                else:
                                    self.show_message("Catch failed!")
                                    player_turn = False

      
            if not player_turn:
                pygame.time.wait(1000)  
                self.enemy_turn()
                if self.enemy_pokemon.health > 0:
                    self.enemy_pokemon.gain_experience(5)
                player_turn = True

            if self.check_game_over():
                pygame.time.wait(3000)
                running = False

            self.screen.fill(WHITE)
            self.player_pokemon.draw(self.screen)
            self.enemy_pokemon.draw(self.screen)
            self.draw_menu()
            self.draw_message()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
