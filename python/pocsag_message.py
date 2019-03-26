"""
    Module that contains the class for a pocsag message.
    A pocsag message is a combination of all message codewords between an address and another address or idle frame.
    Also includes the address codeword.
"""
import binascii
from pocsag_frame import PocsagAddressWord, PocsagMessageWord, PocsagIdleFrame

MESSAGE_TYPES = ["bcd", "alphanum"]
BCD_SPECIAL_CHARS = ["", "U", " ", "-", ")", "("]


class PocsagMessage(object):
    def __init__(self, address):
        """
            address - PocsagAddressWord that it is sent to
            message - concatenation of bits that are the message between addr and idle or new addr
            message_codewords - the PocsagMessageWords that make the message (not used now but could be helpful)
            message_type - enum of MESSAGE_TYPES depending on what we think it is
            message_out - ascii or bcd encoded message 
        """
        self.address = address
        self.message = ""
        self.message_codewords = []
        self.message_type = ""
        self.message_out = ""
        self.bcd_out = ""

    def add_payload(self, message):
        """
            Add a message payload to the message
            args:
                message - (PocsagMessageWord) the message codeword
        """
        self.message_codewords.append(message)
        self.message += message.msg

    def read_message(self):
        raise NotImplementedError("not done yet")

    def read_alphanum(self):
        """ TEMP method to read alphanum for debug"""
        self._decode_alphanum_message()
        print self.message_out

    def read_bcd(self):
        """TEMP method to read bcd for debug"""
        self._decode_bcd_message()
        print self.bcd_out

    def _determine_message_type(self):
        raise NotImplementedError

    def _decode_alphanum_message(self):
        """
            Method to decode message as alphanumeric
            Walks through self.message 7 bits at a time
            Turns that into 2 bytes and ascii encodes it
            Adds resulting char to 
        """
        char_cnt = 0

        # TODO: have to account for null strings that may be less than 7 bits
        # TODO: look into if the ascii converter matches what we expect. seems off rn
        while char_cnt * 7 < len(self.message):
            char = self.message[char_cnt * 7: (char_cnt + 1) * 7]

            # flip bits since they are lsb for alphanum messages
            # also add a 0 at the beginning since they use 7 bit
            # ascii, but binascii uses 2 byte (8 bit)
            char = '0' + char[::-1]
            hex_char = ('%x' % int(char, 2)).zfill(2)

            self.message_out += binascii.unhexlify(hex_char)
            char_cnt += 1

    def _decode_bcd_message(self):
        """
            Method to decode message as numeric bcd message
            4 bit BCD symbols, 5 to a message (20 bit messages)

            Most significant char is the last one (bits 30-27)
            So we need to add new chars to the front, not back

            0x0 - 0x9 are just the digit in the hex value
            0xA = reserved (just make it "")
            0xB = "U"
            0xC = " "
            0xD = "-"
            0xE = ")"
            0xF = "("

            NOTE: trailing a 0xC to each byte should make it translate
            right to ascii (at least for numbers), might try this later
            but it shouldn't matter much since we get the digit anyways
        """
        idx = 0

        while idx < len(self.message) - 20:
            bcd_message = self.message[idx: idx + 20]
            bcd_text = ""

            # put the message into bytes
            for i in range(5):
                bcd_byte = bcd_message[i*4: (i + 1)*4]

                if len(bcd_byte) == 4:
                    bcd_val = int(bcd_byte, 2)
                    if bcd_val < 10:
                        bcd_text = str(bcd_val) + bcd_text
                    else:
                        # use BCD_SPECIAL_CHARS
                        bcd_text = BCD_SPECIAL_CHARS[bcd_val - 10] + bcd_text

                else:
                    print "Error: byte less than 4 bits"

            idx += 20

            self.bcd_out += bcd_text
