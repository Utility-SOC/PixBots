# PixelBots

A deep, tactical roguelike where you build and upgrade your bot's internal circuitry to survive hostile, procedurally generated missions.

## Installation

1.  Ensure you have Python 3.10+ installed.
2.  Install dependencies:
    ```bash
    git clone https://github.com/Utility-SOC/PixBots.git
    cd PixBots
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Run the game:
    ```bash
    python main.py
    ```

## Core Gameplay
PixelBots bridges the gap between mechanical puzzle-solving and tactical combat:
- **The Garage**: Your peaceful hub. Distribute resources, upgrade your stats, and design your Bot's energy flow.
- **The Hex Editor**: Open your components in the Garage to route raw energy through splitters, amplifiers, and resonators to create massive elemental weapon synergies.
- **The Missions**: Deploy to procedurally generated, objective-based maps (Assault, Extraction, Assassination, Labyrinth) built from JSON templates. 
- **Procedural Foes**: Enemies dynamically adapt to your play style, and their sprites (as well as yours) are procedurally generated based on their equipped elemental cores.

## Controls

### The Garage & Menus
- **WASD / Arrow Keys**: Navigate Menus / Cycle Components
- **Enter**: Select / Equip
- **E**: Open Component Hex-Editor (when viewing a component)
- **Escape**: Return to previous menu / Exit game

### Hex Editor
- **Left Click**: Place Selected Tile
- **Right Click**: Delete Tile
- **R**: Rotate Tile (if applicable)
- **C**: Configure Tile (e.g., set Splitter output directions)
- **Escape**: Save and Return to Component Viewer

### Combat Deployment
- **WASD**: Move your Bot
- **Mouse Aim**: Aim weapons
- **Left Click**: Fire / Interact
- **Escape**: Pause Menu

## Debug Controls
> [!NOTE]
> These are for development and testing.

- **F1**: Help Screen
- **F2**: Debug Spawn Menu (Cores, Enemies, Rarities)
- **F4**: Spawn Phalanx Squad
- **F6**: Spawn Enemy Cohort + Boss
- **F7**: Equip Multi-Vector Test Weapon (5x5 Grid)
- **F8**: Equip Full Legendary Gear
- **F9**: Quick Load Game
- **F10**: Print Panic Debug State to Console

## Modding
PixelBots is designed to be highly datadriven. You can freely modify the JSON files in the `/data/` directory to create new game experiences without writing Python:
- `/data/maps/`: Design new mission types and map rules.
- `/data/components.json`: Add new equipment.
- `/data/synergies.json`: Create new elemental combinations.

## Building the Executable

If you want to build a standalone executable `.exe` file for Windows:

### Required Tools
- **Python 3.10+**
- **pip** (Python package installer)
- **PyInstaller**: `pip install pyinstaller`

### Build Instructions
1. Install PyInstaller into your environment:
   ```bash
   python -m pip install pyinstaller
   ```
2. Build the game using the provided `PixBots.spec` file (which includes all necessary assets and data folders):
   ```bash
   pyinstaller PixBots.spec
   ```
3. The compiled executable will be located in the `dist/PixBots` directory. You can run `PixBots.exe` directly from there or package the entire folder into a `.zip` file for distribution.
