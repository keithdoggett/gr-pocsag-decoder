"""
    Module to make PocsagFrames

    Includes a class for the actual frame
    as well as classes for the 2 codewords in each frame
"""
IDLE_FRAME_CODE = "01111010100010011100000110010111"


class PocsagFrame(object):
    def __init__(self, frame_bits, frame_pos):
        self.frame = frame_bits
        self.frame_pos = frame_pos
        self.codewords = []
        self.is_valid = self._is_valid(frame_bits, frame_pos)

    def _is_valid(self, frame_bits, frame_pos):
        """
            Determine if the frame is valid

            args:
                frame_bits - (str) bits representing the frame
                frame_pos - (int) position of frame in batch (0-7)
            returns:
                (bool) of validity
        """
        if len(frame_bits) != 64:
            return False
        elif frame_pos < 0 or frame_pos > 7:
            return False
        else:
            return True

    def get_codewords(self):
        """
            Method to get 2 codewords from the frame

            sets self.codewords to array of len 2 with codewords
        """
        first_word_bits = self.frame[0:32]
        second_word_bits = self.frame[32:64]

        # decide first codeword
        if first_word_bits == IDLE_FRAME_CODE:
            self.codewords.append(PocsagIdleFrame())
        elif first_word_bits[0] == '0':
            self.codewords.append(PocsagAddressWord(
                first_word_bits, self.frame_pos))
        else:
            self.codewords.append(PocsagMessageWord(first_word_bits))

        # decide second frame
        if second_word_bits == IDLE_FRAME_CODE:
            self.codewords.append(PocsagIdleFrame())
        elif second_word_bits[0] == '0':
            self.codewords.append(PocsagAddressWord(
                second_word_bits, self.frame_pos))
        else:
            self.codewords.append(PocsagMessageWord(second_word_bits))


class PocsagCodeWord(object):
    """
        Abstract class for codewords
    """

    def __init__(self, word):
        self.word = word
        self.bch_check = word[21:31]
        self.parity = word[31]
        self.valid = self._is_valid()

    def _is_valid(self):
        """
            Method to perform a BCH check on the codeword

            Uses parity bit to check validity
            Even parity bit means that the total # of 1s should be even

            returns:
                (bool) - result of even parity check
        """
        is_valid = self.word.count("1") % 2 == 0
        if is_valid:
            return True
        else:
            print "invalid", self.word, self.word.count("1"), self.parity
            return False

    def get_data(self):
        raise NotImplementedError(
            'PocsagCodeWord is an abstract class, use PocsagAddressWord or PocsagMessageWord instead')


class PocsagAddressWord(PocsagCodeWord):
    """
        Address codewords have the following bit layout
        | +++++++++++++++++++++++++++++++++++++++++++++++|
        | 1  | 2 - 19    | 20 - 21  | 22 - 31   | 32     |
        | id | addr bits | function | bch check | parity |
        | +++++++++++++++++++++++++++++++++++++++++++++++|

        To derive the address, use the addr bits and frame_pos
        The addr bits are the MSBs while the frame_pos are LSBs

        For example: addr = 111111111000000000, frame = 7
        address = 111111111000000000 + 111 => 111111111000000000111
    """

    def __init__(self, word, frame_pos):
        super(PocsagAddressWord, self).__init__(word)
        self.addr = ""
        self.function = ""
        self.frame_pos = frame_pos
        self._get_data()

    def _get_data(self):
        self.addr = self.word[1:19]
        self.function = self.word[19:21]


class PocsagMessageWord(PocsagCodeWord):
    """
        Message codewords have the following bit layout
        | ++++++++++++++++++++++++++++++++++++|
        | 1  | 2 - 21    | 22 - 31   | 32     | 
        | id | msg bits  | bch check | parity |
        | ++++++++++++++++++++++++++++++++++++|
    """

    def __init__(self, word):
        super(PocsagMessageWord, self).__init__(word)
        self.msg = ""
        self._get_data()

    def _get_data(self):
        self.msg = self.word[1:21]


class PocsagIdleFrame(object):
    def __init__(self):
        self.word = IDLE_FRAME_CODE
