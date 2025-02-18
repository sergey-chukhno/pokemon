import pygame
import time
from config import *

class Evolution:
    def __init__(self, screen, pokemon, evolved_form):
        self.screen = screen
        self.pokemon = pokemon
        self.evolved_form = evolved_form
        self.animation_done = False
        self.start_time = time.time()
        self.font = pygame.font.Font(None, 48)
        
    def draw_evolution_animation(self):
        current_time = time.time() - self.start_time
        animation_duration = 3.0  
        
        if current_time >= animation_duration:
            self.animation_done = True
            return
            
        self.screen.fill(WHITE)
        
        # Calculate progress of animation
        progress = min(current_time / animation_duration, 1.0)
        
        # Draw original Pokemon sprite with fade out
        alpha = int(255 * (1 - progress))
        original_sprite = self.pokemon.sprite.copy()
        original_sprite.set_alpha(alpha)
        
        # Draw evolved form sprite with fade in
        evolved_sprite = self.evolved_form.sprite.copy()
        evolved_sprite.set_alpha(int(255 * progress))
        
        sprite_x = WINDOW_WIDTH // 2 - self.pokemon.sprite.get_width() // 2
        sprite_y = WINDOW_HEIGHT // 2 - self.pokemon.sprite.get_height() // 2
        
        self.screen.blit(original_sprite, (sprite_x, sprite_y))
        self.screen.blit(evolved_sprite, (sprite_x, sprite_y))
        
        text = self.font.render("Evolution in progress...", True, BLACK)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 50))
        self.screen.blit(text, text_rect)
        
        self.draw_sparkles(progress)
        
        pygame.display.flip()
        
    def draw_sparkles(self, progress):
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        for i in range(20):
            angle = (i / 20) * 360 + (progress * 720)  # Rotate twice during animation
            radius = 100 + progress * 50  # Expand radius during animation
            
            x = center_x + radius * pygame.math.Vector2().from_polar((1, angle))[0]
            y = center_y + radius * pygame.math.Vector2().from_polar((1, angle))[1]
            
        
            color = (255, 255, 0)  
            size = int(5 * (1 - abs(progress - 0.5) * 2)) 
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)
            
    def run(self):
        while not self.animation_done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
            self.draw_evolution_animation()
            pygame.time.Clock().tick(60)
            
        return self.evolved_form 