# Games and emulator settings

The image installs RetroArch and the following cores. Put your own games in the corresponding folder, then restart EmulationStation. Empty systems are hidden. File extensions are accepted in lower or upper case. The image contains no game ROMs or commercial BIOS files.

| System | Folder under `/roms` | Core | Formats |
| --- | --- | --- | --- |
| Game Boy / Game Boy Color | `gb` / `gbc` | Gambatte | `.gb` / `.gbc` |
| NES / Famicom Disk System | `nes` | FCEUmm | `.nes`, `.fds`, `.unif`, `.unf` |
| Super Nintendo | `snes` | Snes9x | `.sfc`, `.smc` |
| Game Boy Advance | `gba` | mGBA | `.gba` |
| Master System / Game Gear | `mastersystem` / `gamegear` | Genesis Plus GX | `.sms` / `.gg` |
| Mega Drive / Genesis | `megadrive` | Genesis Plus GX | `.md`, `.gen`, `.bin`, `.smd` |
| Sega CD | `segacd` | Genesis Plus GX | `.cue`, `.chd` |
| PC Engine / TurboGrafx-16 | `pcengine` | Beetle PCE Fast | `.pce` |
| PC Engine CD | `pcenginecd` | Beetle PCE Fast | `.cue`, `.chd` |
| PlayStation | `psx` | PCSX ReARMed | `.cue`, `.chd`, `.pbp`, `.m3u`, `.exe` |
| Nintendo 64 | `n64` | Mupen64Plus-Next | `.z64`, `.n64`, `.v64` |
| Dreamcast | `dreamcast` | Flycast 2021 | `.gdi`, `.cue`, `.chd`, `.cdi`, `.m3u` |
| PSP | `psp` | PPSSPP | `.iso`, `.cso`, `.chd`, `.pbp`, `.elf`, `.prx` |
| Arcade / Neo Geo | `arcade` / `neogeo` | FinalBurn Neo | `.zip`, `.7z` |

Keep disc track files alongside their `.cue` or `.gdi` descriptor. For multidisc PS1 and Dreamcast games, use an `.m3u` playlist containing relative paths to each disc. Arcade archives must match the installed FinalBurn Neo revision; arbitrary MAME sets are not interchangeable. Its source revision is pinned in the package Makefile.

## BIOS and support files

Put BIOS files in `/roms/bios`. Names are case sensitive. Sega CD requires `bios_CD_U.bin`, `bios_CD_E.bin` or `bios_CD_J.bin` for the game's region; PC Engine CD requires `syscard3.pce`. Famicom Disk System uses `disksys.rom`. PCSX ReARMed and Flycast provide high-level BIOS emulation, but some games need a compatible original BIOS. Neo Geo games need the matching `neogeo.zip` alongside the game archive or in the core's BIOS search location.

PPSSPP's redistributable fonts and support files are installed in `/usr/share/retroarch/system/PPSSPP`. The launcher links them into `/roms/bios/PPSSPP` when that path is absent, or copies them on FAT/exFAT cards. FinalBurn Neo's high-score database is installed similarly under `fbneo`. Existing user directories are preserved. This also works after mounting a separate games card at `/roms`.

## Controls and saves

Default handheld mappings use **Select + Start** to exit, **Select + X** for the RetroArch menu, **Select + L** to load a state and **Select + R** to save a state. Check the active controller's mapping before relying on save-state shortcuts. Exit the emulator and shut down through EmulationStation before removing a card or cutting power.

Battery saves and memory cards use `/roms/saves/<system>`; save states use `/roms/states/<system>`. Systems have separate directories, so identically named games from different systems do not share saves. RetroArch periodically flushes cartridge save RAM and saves again on a normal exit. Emulator save states are tied to the core and its version; keep in-game saves as well.

Global settings live in `/etc/retroarch.cfg`, core defaults in `/etc/retroarch-core-options.cfg`, and per-game/core overrides in `/root/.config/retroarch`. These settings survive a configuration-preserving sysupgrade. ROMs, artwork, BIOS files and saves on the OS card are not part of OpenWrt's configuration backup; use a separate games card or back them up before upgrading.

N64, Dreamcast and PSP default to native rendering resolutions with ARM64 dynamic recompilers. Speed and compatibility depend on the game. Their presence in an image is not a full-speed performance claim; record hardware results using [TESTING.md](TESTING.md).

Launch failures appear in EmulationStation. For more detail, inspect `/tmp/handheld/retroarch.log` over SSH. The launcher checks for missing files, required CD BIOS files and writable save storage before starting a game.

## Maintaining the system list

`package/games/retroarch/files/systems.tsv` maps each system to its core and extensions. Run `python3 scripts/rk3326-systems.py` after editing it to update the default EmulationStation configuration. CI checks that the generated file matches and loads every listed core from the packaged filesystem.
