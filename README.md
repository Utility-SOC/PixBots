# PixelBots Enhanced

A tactical hex-grid based roguelike where you build and upgrade your bot to survive hostile biomes.

## Installation

1.  Ensure you have Python 3.10+ installed.
2.  Install dependencies:
    ```bash
    python -m venv PixBots
    git pull https://github.com/Utility-SOC/PixBots
    cd PixBots
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
