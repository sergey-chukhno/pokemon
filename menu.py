import pygame

class MainMenu:
    def __init__(self, screen, fonts, colors):
        self.screen = screen
        self.font = fonts['font']
        self.colors = colors
        self.menu_items = ["New Game", "Load Game", "Exit"]
        self.selected_item = 0

    def draw(self):
        self.screen.fill(self.colors['white'])
        title = self.font.render("Pokemon Game", True, self.colors['black'])
        title_rect = title.get_rect(center=(400, 100))
        self.screen.blit(title, title_rect)

        for index, item in enumerate(self.menu_items):
            color = self.colors['black'] if index == self.selected_item else self.colors['grey']
            menu_text = self.font.render(item, True, color)
            menu_rect = menu_text.get_rect(center=(400, 200 + index * 50))
            self.screen.blit(menu_text, menu_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN:
                selected_item = self.menu_items[self.selected_item]
                if selected_item == "New Game":
                    # Réinitialiser le jeu
                    return "New Game"
                elif selected_item == "Load Game":
                    # Charger l'état du jeu
                    return "Load Game"
                elif selected_item == "Exit":
                    return "Exit"
        return None