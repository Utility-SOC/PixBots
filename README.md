# PixelBots Enhanced

A tactical hex-grid based roguelike where you build and upgrade your bot to survive hostile biomes.

## Installation

1.  Ensure you have Python 3.10+ installed.
2.  Install dependencies:
    ```bash
    python -m venv PixBots
    git pull https://github.com/Utility-SOC/PixBots
    cd PixBots
    .\Scripts\activate.ps1
    pip install -r requirements.txt
    ```
3.  Run the game:
    ```bash
    python main.py
    ```

## Controls

### General
-   **WASD / Arrow Keys**: Move Camera / Navigate
-   **Esc**: Pause / Menu
-   **F1**: Toggle Debug Info
-   **F5**: Quick Save
-   **F9**: Quick Load

### Combat / Exploration
-   **Left Click**: Move / Interact
-   **Space**: Skip Turn / Wait
-   **I**: Open Inventory/Component Viewer

### Component Editor (Hex Grid)
-   **Right Click**: Open Editor (on a component in Viewer)
-   **Left Click**: Place Tile
-   **Right Click**: Rotate Tile (or Delete if Shift is held)
-   **1-7**: Select Tile Type
    -   1: Conduit
    -   2: Amplifier
    -   3: Resonator
    -   4: Splitter
    -   5: Reflector
    -   6: Weapon Mount
    -   7: Super Conduit
-   **E**: Toggle Splitter Configuration Mode (Hover over Splitter)
-   **S**: Cycle Reflector/Filter Synergy (Hover over Reflector)

## Features
-   **Hex-Based Component System**: Design your internal energy flow.
-   **Procedural Biomes**: Explore Forest, Desert, Ice, and Volcanic regions.
-   **Crafting**: Scavenge parts and upgrade your systems.
-   **Synergies**: Combine elemental effects (Fire, Ice, Lightning, etc.) for massive damage.

## Debug Controls
> [!NOTE]
> These controls are for development and testing purposes.

-   **F1**: Help Screen
-   **F5**: Quick Save
-   **F6**: Spawn Enemy Cohort (5-8 enemies)
-   **F7**: Equip Multi-Vector Test Weapon (Legendary Arm)
-   **F8**: Equip Full Legendary Gear Set
-   **F9**: Quick Load
-   **F10**: Toggle Boss Invulnerability
-   **I**: Open Debug Spawn Menu (Spawn Items, Enemies, Cores)
-   **J**: Open Debug Biome Switcher
-   **R**: Open Reactor Debug Menu
-   **B**: Spawn Random Enemy at Cursor

## Roadmap
1.  **Enhanced Procedural Generation**: Further refine enemy and biome generation with more unique parts and themes.
2.  **Synergy Expansion**: Add more elemental combinations and complex status effects.
3.  **Boss Mechanics**: Implement unique AI behaviors and phases for the new procedural bosses.
4.  **Audio Overhaul**: Add sound effects and dynamic music layering based on combat intensity.
5.  **UI Polish**: Improve menus, tooltips, and visual feedback for synergies.
6.  **Save System Robustness**: Ensure all game state (including projectiles and particles) is persisted.
