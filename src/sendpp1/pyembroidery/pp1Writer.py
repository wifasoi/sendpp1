from enum import Enum
from pyembroidery.EmbConstant import *
from pyembroidery.WriteHelper import write_int_16le
from pyembroidery.EmbPattern import EmbPattern
# COLOR_FLAG = 3
# END_FLAG = 5

# FEED = 1
# CUT = 2
# JUMP = FEED | CUT

class EmbCommand(Enum):
    STITCH = STITCH
    JUMP = JUMP
    TRIM = TRIM
    COLOR_CHANGE = COLOR_CHANGE
    END = END

def write_point(f, coordinate: int, flag: int):
    write_int_16le(f, (coordinate << 3) | (flag & 0x07))

def encode_stitch(f, x: int, y: int, block_flag: int, stitch_flag):
    """Encode a normal stitch, optionally marking it as a jump or cut."""
    write_point(f,x, block_flag)
    write_point(f,y, stitch_flag)


def write(pattern, f, settings=None):
    """Iterate through an EmbPattern and encode all operations."""
    for x_abs,y_abs,cmd in pattern.stitches:
        
        match EmbCommand(cmd):
            case EmbCommand.STITCH:
                encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=0)
            case EmbCommand.JUMP:
                encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=3)
            case EmbCommand.TRIM:
                encode_stitch(f, x_abs, y_abs, block_flag=0, stitch_flag=2)
            case EmbCommand.COLOR_CHANGE:
                encode_stitch(f, x_abs, y_abs, block_flag=3, stitch_flag=0)
            case EmbCommand.END:
                encode_stitch(f, x_abs, y_abs, block_flag=5, stitch_flag=0)

