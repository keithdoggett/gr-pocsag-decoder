"""
    Module to read pocsag batches and interpret them

    Batches have this layout

    | +++++++++++++++++++++++++++++++++++ |
    | 1-32 |         33 - 512             |
    |  FSC | 8 frames (16 codewords)      |
    | +++++++++++++++++++++++++++++++++++ |

    where the FSC is FRAME_SYNC_CODE, basically a code
    that identifies we are at the beginning of a batch.

    There can be many concurrent batches depending on the
    length of the message
"""
from pocsag_frame import PocsagFrame
FRAME_SYNC_CODE = "01111100110100100001010111011000"


class PocsagBatch(object):
    """
        args:
            batch - (str) of len 544 bits (32 * 16 + 32)
    """

    def __init__(self, batch):
        self.batch = batch
        self.is_valid = self._is_valid(batch)
        self.frames = []

    def _is_valid(self, batch):
        """
            Method to determine if it is a valid batch
            Will check length and the existance of an FSC at the beginning

            args:
                batch - (str) the batch of bits
            returns:
                (bool) identifying validity
        """
        # print batch[0:32]
        if len(batch) != 544:
            print "invalid batch len"
            return False
        elif batch[0:32] != FRAME_SYNC_CODE:
            # print "invalid FSC", batch[0:32], '{0:b}'.format(int(
            #     batch[0:32], 2) >> 1 ^ int(FRAME_SYNC_CODE, 2))
            return False
        else:
            return True

    def parse_frames(self):
        """
            Method to parse frames into self.frames as PocsagFrame objects
        """
        idx = 32  # start at bit 33, after fsc
        frame_pos = 0
        while idx < len(self.batch):
            frame_bits = self.batch[idx: idx + 64]
            frame = PocsagFrame(frame_bits, frame_pos)
            frame.get_codewords()

            self.frames.append(frame)
            idx += 64
            frame_pos += 1


def contains_fsc(bits):
    """
        Function to determine if a bitstring contains the fsc
        at the beginning

        args:
            bits - (str) of the bits
        returns:
            (bool) of whether it has the fsc at the beginning
    """
    return bits[0:32] == FRAME_SYNC_CODE
