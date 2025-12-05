import pygame
import constants
from equipment.component import ComponentEquipment

class EquipmentMenu:
    """UI for managing equipment and inventory."""
    def __init__(self, screen, asset_manager, player):
        self.screen = screen
        self.asset_manager = asset_manager
        self.player = player
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 36)
        
        self.selected_index = 0
        self.message = "Select an item to equip/unequip"

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.player.inventory) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_e:
                self.try_equip()
        return None

    def try_equip(self):
        if not self.player.inventory:
            self.message = "No items in inventory"
            return
            
        if self.selected_index >= len(self.player.inventory):
            return
            
        item = self.player.inventory[self.selected_index]
        
        # Check for existing item in that slot
        old_item = self.player.components.get(item.slot)
        
        # Attempt to equip
        if self.player.equip_component(item):
            # Remove from inventory after equipping
            self.player.inventory.pop(self.selected_index)
            
            # Add old item back to inventory
            if old_item:
                self.player.inventory.append(old_item)
                self.message = f"Equipped: {item.name}. Returned: {old_item.name}"
            else:
                self.message = f"Equipped: {item.name}"
            
            # Adjust selection if needed
            if self.selected_index >= len(self.player.inventory):
                self.selected_index = max(0, len(self.player.inventory) - 1)
        else:
            self.message = f"Cannot equip: {item.name} (slot occupied?)"

    def draw(self):
        self.screen.fill((30, 30, 40))
        
        # Title
        title = self.title_font.render("Equipment & Inventory", True, (255, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # Message
        msg = self.font.render(self.message, True, (255, 255, 0))
        self.screen.blit(msg, (20, 60))
        
        # Equipped items section
        y = 120
        equipped_title = self.font.render("=== EQUIPPED ===", True, (100, 255, 100))
        self.screen.blit(equipped_title, (20, y))
        y += 35
        
        slots = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "back"]
        for slot in slots:
            comp = self.player.components.get(slot)
            if comp:
                text = f"{slot.replace('_', ' ').title()}: {comp.name} ({comp.quality})"
                color = (200, 255, 200)
            else:
                text = f"{slot.replace('_', ' ').title()}: [Empty]"
                color = (100, 100, 100)
            
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (40, y))
            y += 25
        
        # Inventory section
        y += 20
        inv_title = self.font.render("=== INVENTORY ===", True, (100, 200, 255))
        self.screen.blit(inv_title, (20, y))
        y += 35
        
        if not self.player.inventory:
            no_items = self.font.render("(No items)", True, (150, 150, 150))
            self.screen.blit(no_items, (40, y))
        else:
            for i, item in enumerate(self.player.inventory):
                color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
                prefix = ">> " if i == self.selected_index else "   "
                text = f"{prefix}{item.name} [{item.slot}] ({item.quality})"
                surf = self.font.render(text, True, color)
                self.screen.blit(surf, (40, y))
                y += 25
        
        # Instructions
        instructions = self.font.render("↑/↓: Select | ENTER/E: Equip | ESC: Close", True, (150, 150, 150))
        self.screen.blit(instructions, (20, self.screen.get_height() - 40))
