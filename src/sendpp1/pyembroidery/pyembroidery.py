from pyembroidery.EmbPattern import EmbPattern
import sendpp1.pyembroidery.pp1Writer as Pp1Writer

@staticmethod
def write_pp1_f(pattern, stream, settings=None):
    """Writes fileobject as PES file"""
    EmbPattern.write_embroidery(Pp1Writer, pattern, stream, settings)

EmbPattern.write_pp1 = write_pp1_f

write_pp1 = EmbPattern.write_pp1