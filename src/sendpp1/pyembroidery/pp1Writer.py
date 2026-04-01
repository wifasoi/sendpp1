"""PP1 stitch-data writer — converts an EmbPattern into the PP1 binary format.

Each stitch command is 4 bytes: x_raw (int16 LE) + y_raw (int16 LE)
    x = x_raw >> 3   (absolute coordinate)
    section = x_raw & 0x07  (0=normal, 3=color change, 5=end)
    y = y_raw >> 3   (absolute coordinate)
    operation = y_raw & 0x07  (0=stitch, 1=feed, 2=cut, 3=jump)
"""

from loguru import logger
from pyembroidery.EmbConstant import (
    STITCH, JUMP, TRIM, COLOR_CHANGE, END, STOP, COMMAND_MASK,
    SEW_TO, NEEDLE_AT, SEQUENCE_BREAK, COLOR_BREAK, STITCH_BREAK,
    TIE_ON, TIE_OFF,
)
from pyembroidery.WriteHelper import write_int_16le


def write_point(f, coordinate: int, flag: int):
    write_int_16le(f, (coordinate << 3) | (flag & 0x07))


def encode_stitch(f, x: int, y: int, block_flag: int, stitch_flag: int):
    """Encode a single 4-byte PP1 stitch command."""
    write_point(f, x, block_flag)
    write_point(f, y, stitch_flag)


def write(pattern, f, settings=None):
    """Iterate through an EmbPattern and encode all operations.

    pyembroidery commands pack needle/thread info in upper bytes.
    We mask with COMMAND_MASK (0xFF) to get the core command type.
    """
    for x_abs, y_abs, raw_cmd in pattern.stitches:
        cmd = raw_cmd & COMMAND_MASK

        if cmd == STITCH:
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=0)
        elif cmd == JUMP:
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=3)
        elif cmd == TRIM:
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=2)
        elif cmd == COLOR_CHANGE:
            encode_stitch(f, x_abs, y_abs, block_flag=3, stitch_flag=0)
        elif cmd == STOP:
            # STOP is like a pause / color change on the PP1
            encode_stitch(f, x_abs, y_abs, block_flag=3, stitch_flag=0)
        elif cmd == END:
            encode_stitch(f, x_abs, y_abs, block_flag=5, stitch_flag=0)
        elif cmd in (SEW_TO, NEEDLE_AT):
            # Treat repositioning as a regular stitch
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=0)
        elif cmd in (TIE_ON, TIE_OFF):
            # Tie commands → encode as a stitch at the same position
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=0)
        elif cmd in (SEQUENCE_BREAK, COLOR_BREAK, STITCH_BREAK):
            # Break commands signal section boundaries — treat as trim
            encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=2)
        else:
            # Skip control/meta commands (matrix ops, settings, etc.)
            logger.trace("Skipping unsupported pyembroidery cmd {} at ({}, {})", raw_cmd, x_abs, y_abs)
