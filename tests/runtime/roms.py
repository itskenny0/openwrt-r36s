"""Generate original, minimal console programs for emulator smoke tests.

These contain no commercial game, logo, or BIOS data. Each program runs a
short instruction sequence and then loops. The colour tests exercise CPU,
memory-mapped video registers, and the core's frame callback together.
"""
from pathlib import Path
import struct


def game_boy():
    rom = bytearray(32768)
    rom[0x100:0x104] = bytes.fromhex("00 c3 50 01")
    rom[0x134:0x140] = b"OPENWRT TEST".ljust(12, b" ")
    rom[0x147] = 3  # MBC1 + battery-backed RAM
    rom[0x149] = 2  # 8 KiB RAM
    # Store 0x5a on a fresh cartridge, 0x5b if a frontend restored its last save.
    program = bytes.fromhex("3e 0a ea 00 00 fa 00 a0 fe 5a 20 04 3e 5b 18 02 3e 5a ea 00 a0 18 fe")
    rom[0x150:0x150 + len(program)] = program
    rom[0x14d] = (-sum(rom[0x134:0x14d]) - 25) & 255
    return rom


def nes():
    header = b"NES\x1a" + bytes([2, 1, 2, 0]) + bytes(8)
    prg = bytearray(32768)
    program = bytearray.fromhex(
        "78 d8 a2 00 8e 00 20 8e 01 20 "  # SEI, CLD, disable rendering
        "2c 02 20 10 fb 2c 02 20 10 fb "  # Wait through PPU warm-up
        "a9 3f 8d 06 20 a9 00 8d 06 20 "  # PPUADDR = palette entry 0
        "a9 16 8d 07 20 "                 # Red backdrop
        "a9 5a 8d 00 60 "                 # Battery RAM marker
        "a9 0a 8d 01 20")                 # Enable background
    loop = 0x8000 + len(program)
    program += b"\x4c" + struct.pack("<H", loop)
    prg[:len(program)] = program
    struct.pack_into("<HHH", prg, 32762, loop, 0x8000, loop)
    return header + prg + bytes(8192)


def snes():
    rom = bytearray(131072)
    program = bytes.fromhex(
        "78 18 fb e2 20 "             # SEI, CLC, XCE, 8-bit accumulator
        "a9 00 8d 21 21 "            # CGRAM entry 0
        "a9 1f 8d 22 21 a9 00 8d 22 21 "  # Red backdrop
        "a9 0f 8d 00 21 "            # Unblank at full brightness
        "a9 5a 8f 00 00 70 "         # Battery RAM marker
        "80 fe")                    # BRA to self
    rom[:len(program)] = program
    rom[0x7fc0:0x7fd5] = b"OPENWRT TEST".ljust(21, b" ")
    rom[0x7fd5:0x7fdb] = bytes([0x20, 2, 7, 3, 1, 0])
    struct.pack_into("<H", rom, 0x7ffc, 0x8000)
    checksum = (sum(rom) + 510) & 65535
    struct.pack_into("<HH", rom, 0x7fdc, checksum ^ 65535, checksum)
    return rom


def gba():
    rom = bytearray(32768)
    struct.pack_into("<I", rom, 0, 0xea00002e)  # ARM branch to 0xc0
    rom[0xa0:0xac] = b"OPENWRT TEST".ljust(12, b" ")
    rom[0xac:0xb2] = b"OWRT00"
    rom[0xb2] = 0x96
    rom[0xbd] = (-sum(rom[0xa0:0xbd]) - 0x19) & 255
    # Mode 3 + BG2, one red pixel, a byte in SRAM, then an ARM branch loop.
    words = [0, 0, 0xe1c010b0, 0, 0xe3a0101f, 0xe1c010b0,
             0, 0xe3a0105a, 0xe5c01000, 0xeafffffe]
    for instruction, register, value in ((0, 0, 0x04000000), (1, 1, 0x403),
                                         (3, 0, 0x06000000), (6, 0, 0x0e000000)):
        offset = len(words) * 4 - instruction * 4 - 8
        words[instruction] = 0xe59f0000 | register << 12 | offset
        words.append(value)
    struct.pack_into("<" + "I" * len(words), rom, 0xc0, *words)
    rom[0x200:0x209] = b"SRAM_V113"
    return rom


def megadrive():
    rom = bytearray(32768)
    struct.pack_into(">II", rom, 0, 0x00fffe00, 0x200)
    rom[0x100:0x110] = b"SEGA MEGA DRIVE "
    rom[0x120:0x150] = b"OPENWRT TEST".ljust(48, b" ")
    rom[0x150:0x180] = rom[0x120:0x150]
    struct.pack_into(">IIII", rom, 0x1a0, 0, len(rom) - 1, 0xff0000, 0xffffff)
    rom[0x1b0:0x1b4] = bytes.fromhex("52 41 f8 20")
    struct.pack_into(">II", rom, 0x1b4, 0x200001, 0x203fff)
    rom[0x1f0:0x1f3] = b"JUE"
    program = bytes.fromhex(
        "46 fc 27 00 "                        # Disable interrupts
        "33 fc 81 04 00 c0 00 04 "            # Mode 5, display disabled
        "23 fc c0 00 00 00 00 c0 00 04 "      # CRAM address 0
        "33 fc 00 0e 00 c0 00 00 "            # Red backdrop
        "33 fc 81 44 00 c0 00 04 "            # Enable display
        "60 fe")                              # BRA to self
    rom[0x200:0x200 + len(program)] = program
    return rom


def pcengine():
    rom = bytearray(8192)
    program = bytes.fromhex(
        "78 d4 a9 ff 53 01 "      # SEI, high clock, map MPR0 to I/O
        "a9 00 8d 02 04 8d 03 04 "  # VCE palette address 0
        "a9 38 8d 04 04 a9 00 8d 05 04 "  # Red backdrop
        "80 fe")
    rom[:len(program)] = program
    struct.pack_into("<H", rom, 0x1ffe, 0xe000)
    return rom


def playstation():
    image = bytearray(4096)
    image[:8] = b"PS-X EXE"
    struct.pack_into("<IIII", image, 0x10, 0x80010000, 0, 0x80010000, 2048)
    struct.pack_into("<I", image, 0x30, 0x801fff00)
    # MIPS: GPU reset/display mode, red VRAM rectangle, display enable, loop.
    instructions = [
        0x3c081f80, 0x35081810,             # t0 = GP0
        0xad000004,                         # GP1 reset
        0x3c090800, 0x35290001, 0xad090004, # GP1 display mode, 320 pixels
        0x3c090200, 0x352900ff, 0xad090000, # GP0 fill rectangle, red
        0xad000000,                         # Top-left corner
        0x3c090100, 0x35290140, 0xad090000, # 320 x 256 pixels
        0x3c090300, 0xad090004,             # GP1 enable display
        0x1000fff6, 0x00000000,             # Redraw continuously, NOP delay slot
    ]
    struct.pack_into("<" + "I" * len(instructions), image, 0x800, *instructions)
    return image


def write_roms(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    systems = {
        "gambatte": ("gb", game_boy), "fceumm": ("nes", nes),
        "snes9x": ("sfc", snes), "mgba": ("gba", gba),
        "genesis_plus_gx": ("md", megadrive),
        "mednafen_pce_fast": ("pce", pcengine),
        "pcsx_rearmed": ("exe", playstation),
    }
    result = {}
    for core, (extension, build) in systems.items():
        path = directory / (core + "." + extension)
        path.write_bytes(build())
        result[core] = path
    return result
