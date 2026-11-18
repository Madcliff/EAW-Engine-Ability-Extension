# Installing the EAW Engine Ability Extension

This guide is for players. You don't need any programming knowledge.

## Before you start

You need:

- **Star Wars: Empire at War – Gold Pack on Steam**, with *Forces of Corruption*. The patch is made for the current
  64-bit Steam version of `StarWarsG.exe` (1.121.859328). GOG and old disc versions are not supported.
- **A mod that uses the extension**, such as Revan's Revenge (`zz_mod_revrev`). On its own the extension adds
  nothing you will notice. Mods switch its features on with their own `Data/zz_*.txt` files.
- **Windows 10/11**, or **Linux / Steam Deck** running the game through Proton.

Close the game before installing or removing the patch.

## 1. Download

1. Open the [Releases page](https://github.com/Madcliff/EAW-Engine-Ability-Extension/releases) and download the
   newest `EAW-Engine-Ability-Extension-vX.Y.Z.zip`.
2. Extract the zip anywhere, for example to your Desktop. Don't run the installer from inside the zip.

The zip contains:

| File | What it is |
|---|---|
| `ZZ_SWFOC.dll` | The engine extension |
| `Install.bat`, `Uninstall.bat`, `Status.bat` | Windows: double-click these |
| `install.ps1` | The Windows installer that the `.bat` files run |
| `install.sh`, `install.py` | Linux / Steam Deck installer |
| `INSTALL.md`, `LICENSE`, `SHA256SUMS.txt` | This guide, the license and file checksums |

## 2a. Install on Windows

1. Double-click **`Install.bat`**.
2. A black window opens, finds your game through Steam and reports each step. It should end with
   **"Done. Start the game as usual."**
3. Press any key to close the window.

If Windows shows *"Windows protected your PC"*, click **More info → Run anyway**. Windows shows this for any
unsigned script downloaded from the internet.

If the installer says **access denied**, the game is probably installed under `C:\Program Files (x86)`.
Right-click `Install.bat` and choose **Run as administrator**.

## 2b. Install on Linux / Steam Deck

Open a terminal (on Steam Deck: switch to **Desktop Mode** and open **Konsole**). Go to the extracted folder and
run the installer:

```bash
cd ~/Desktop/EAW-Engine-Ability-Extension-v*
```

```bash
./install.sh
```

The installer needs `python3`, which comes with every common Linux distribution and SteamOS. It finds the game in
all your Steam libraries, including Flatpak and Snap Steam. It should end with **"Done. Start the game as usual."**

You don't need a Proton launch option or `WINEDLLOVERRIDES`: the game loads the DLL by itself.

## 3. Play

Start the game from Steam the way your mod tells you to, for example with its launch option
`MODPATH=Mods\zz_mod_revrev`. The extension loads the mod's settings from that mod folder.

To confirm it works, look for `zz_ability_buttons.log` in the game's `corruption` folder after starting the game.
The extension writes it every time it loads.

## After a Steam update or "Verify integrity of game files"

Both of these replace `StarWarsG.exe` with the original, which switches the extension off. **Run the installer
again** (`Install.bat` or `./install.sh`); it takes a second.

## Checking the install

- Windows: double-click **`Status.bat`**
- Linux: `./install.sh status`

The last line says `engine patch is INSTALLED` or `NOT installed`.

## Uninstalling

- Windows: double-click **`Uninstall.bat`**
- Linux: `./install.sh uninstall`

This puts the exe back exactly as Steam shipped it and deletes `ZZ_SWFOC.dll`. A backup of the untouched exe,
`StarWarsG.exe.zz_original`, stays in the `corruption` folder in case you need it; you can delete it. You can also
undo everything with Steam's *Verify integrity of game files*.

## Game not found / installed somewhere unusual

If the installer can't find the game, tell it where the game is. Use the folder named
`Star Wars Empire at War` (the one that contains `corruption`).

Windows, in PowerShell inside the extracted folder:

```
powershell -ExecutionPolicy Bypass -File install.ps1 -GameDir "D:\Games\Steam\steamapps\common\Star Wars Empire at War"
```

Linux:

```bash
./install.sh --game-dir "/path/to/steamapps/common/Star Wars Empire at War"
```

All options:

| Windows (`install.ps1`) | Linux (`install.sh`) | What it does |
|---|---|---|
| *(none)* | `install` *(default)* | Install or update |
| `-Uninstall` | `uninstall` | Remove |
| `-Status` | `status` | Show what is installed |
| `-GameDir <folder>` | `--game-dir <folder>` | Use this game folder instead of searching Steam |
| `-SteamRoot <folder>` | `--steam-root <folder>` | Also search this Steam folder for libraries |
| `-Dll <file>` | `--dll <file>` | Install a different `ZZ_SWFOC.dll` |
| `-Force` | `--force` | Install even if the exe isn't the expected version |

On Windows with Python installed, `py install.py` also works and takes the same options as the Linux column.

## Troubleshooting

**"this StarWarsG.exe is not the Steam 64-bit version 1.121.859328"**
Your exe isn't the version the patch was made for. This usually means a newer Steam update or a non-Steam copy.
`--force` / `-Force` installs anyway. The extension checks every change against the original code first and leaves
out anything that doesn't match (the log lists those). Whether the game works is not guaranteed. Please open an
issue with your exe version.

**The game crashes at startup after installing**
Run the uninstaller (or *Verify integrity of game files*). Then open an
[issue](https://github.com/Madcliff/EAW-Engine-Ability-Extension/issues) and attach `corruption/zz_ability_buttons.log`.

**Nothing seems different in game**
- Make sure the mod is running: check its launch option.
- Run `Status.bat` / `./install.sh status`.
- Read `corruption/zz_ability_buttons.log`. Each feature reports there whether it was switched on.

**Multiplayer**
Multiplayer hasn't been tested. At minimum, every player needs the same mod and the same extension version.

## Is this safe?

- No Windows or system file is touched. Only two things change in the game's `corruption` folder:
  `ZZ_SWFOC.dll` is added, and one 12-byte DLL name inside `StarWarsG.exe` is changed from `POWRPROF.dll` to
  `ZZ_SWFOC.dll`.
- The installers are plain text scripts (`install.ps1`, `install.py`), so you can read exactly what they do.
- `SHA256SUMS.txt` lists the checksum of every file in the release.
- The full source code is in this repository.
