"""
    Program to read pocsag_bits and figure out if it can find any of the codewords I want
"""
import socket
import binascii
from pocsag_batch import PocsagBatch, contains_fsc
from pocsag_frame import PocsagIdleFrame, PocsagMessageWord, PocsagAddressWord
from pocsag_message import PocsagMessage
from udp_interface import UdpInterface

FILE_NAME = "./pocsag_bits"
UDP_IP_ADDR = "127.0.0.1"  # localhost
UDP_PORT = 5125
PAYLOAD_SIZE = 1472  # default GNURadio payload size (in bytes)
PREAMBLE = "10"*288
BATCH_SIZE = 544

# should we use net or file?
FROM_FILE = False


def main():
    """Main method"""
    if FROM_FILE:
        from_file()
    else:
        from_net()


def from_net():
    """
        Main method where we read from udp
    """
    # initialize udp connection
    conn = UdpInterface(UDP_IP_ADDR, UDP_PORT, PAYLOAD_SIZE)
    while True:
        conn.read_socket()
        # print "conn buffer len", len(conn.buffer)

        # TODO: try looking for only FSCs
        # it is possible we are getting bit errors during preamble and it's messing us up
        # hard to say because idk the error rate, but 576 correct in a row seems like a lot
        idx = 0
        while idx < len(conn.buffer) - 576:

            bit_slice = conn.buffer[idx: idx + 576]
            bit_str = ''.join(bit_slice)

            if bit_str == PREAMBLE:
                idx += 576

                # read in more data from socket so that we get the full message
                get_batches(conn, idx)

                batches = group_batches(conn.buffer[idx:])
                parse_batches(batches)

                # if there were batches, increment by 544 bits per batch
                # if the batch wasn't valid, only increment by 1
                if len(batches) != 0:
                    print len(batches)
                    idx += BATCH_SIZE * len(batches)

                    # since we found data, we should remove the previous part of the buffer
                    # because it will just keep repeating this
                    conn.clean_buffer(idx)
                else:
                    idx += 1

            else:
                idx += 1


def from_file():
    """
        Main method where we read from file
    """
    with open(FILE_NAME, mode='rb') as file:
        byte_arr = bytearray(file.read())

    # NOTE: these are LSB, so we will have to reverse are byte sets to match the codewords
    bits = []
    for i in byte_arr:
        # flip bit since high freq is logical 0 and low freq is logical 1
        bit = i ^ 1
        bits.append(str(bit))

     # TODO: try looking for only FSCs
    # it is possible we are getting bit errors during preamble and it's messing us up
    # hard to say because idk the error rate, but 576 correct in a row seems like a lot
    idx = 0
    while idx < len(bits) - 576:

        """"""
        bit_slice = bits[idx: idx + 576]
        bit_str = ''.join(bit_slice)

        if bit_str == PREAMBLE:
            # print "found preamble boi"
            idx += 576
            batches = group_batches(bits[idx:])
            parse_batches(batches)

            # if there were batches, increment by 544 bits per batch
            # if the batch wasn't valid, only increment by 1
            if len(batches) != 0:
                print len(batches)
                idx += BATCH_SIZE * len(batches)

            else:
                idx += 1

        else:
            idx += 1


def get_batches(conn, end_of_preamble):
    """
        Function to keep receiving data from the socket after
        we have found the preamble

        This is necessary because it's likely we haven't received
        the full message with the preamble, so we need to keep getting
        data until we've reached the end of the messages. Will use
        contains_fsc every 544 bits to see if we're still getting batches

        If we need more data, we'll fetch it then keep going.

        args:
            conn - (UdpInterface)
            end_of_preamble - (int) index of where we are in conn.buffer
    """
    end_of_batches = False
    idx = end_of_preamble

    while not end_of_batches:
        # fsc is 32 bits. if we are within that, we need more data
        if idx >= len(conn.buffer) - 32:
            # print "reading more data"
            conn.read_socket()

        batch = conn.buffer[idx: idx + BATCH_SIZE]
        batch_str = ''.join(batch)

        if contains_fsc(batch_str):
            # print "contains fsc"
            idx += BATCH_SIZE

        else:
            end_of_batches = True


def group_batches(bits):
    """
        Group batches once a preamble is identified

        args:
            bits - (array) slice of bits from end of preamble to end
        returns:
            batch[]
    """
    batches = []
    valid_batches = True
    num_batches = 0

    # just keep taking 544 bit slices and batch them
    # if each subsequent batch is valid, keep doing it
    # if not, break
    while valid_batches:
        batch_bits = bits[num_batches *
                          BATCH_SIZE: (num_batches + 1) * BATCH_SIZE]
        batch_bits = ''.join(batch_bits)

        batch = PocsagBatch(batch_bits)

        if batch.is_valid:
            batch.parse_frames()
            batches.append(batch)
            num_batches += 1
        else:
            # print "invalid batch"
            valid_batches = False

    return batches


def parse_batches(batches):
    """
        Function to parse a list of batches
        Will print any data found on it

        Messages in pocsag start with an address (or idle frames then an address)
        after that, there are messages until the batch ends or messages followed by idle frames

        combine all the data for the messages after we see an address

        arg:
            (batch[]) - list of batches from one preamble
    """
    # first, get all the data together
    # iterate through each batch and combine all the Pocsag messages
    # then print out ascii characters
    # will figure out what to do with addresses
    print "******** NEW PREAMBLE *************"
    flattened_codewords = []
    for batch in batches:
        for frame in batch.frames:
            for codeword in frame.codewords:
                flattened_codewords.append(codeword)
                # print type(codeword)

    messages = []
    curr_message = None

    in_message = False
    for codeword in flattened_codewords:
        # addresses are the start of messages
        if in_message is False and isinstance(codeword, PocsagAddressWord):
            in_message = True
            curr_message = PocsagMessage(codeword)

        # another address is start of new message
        elif in_message is True and isinstance(codeword, PocsagAddressWord):
            messages.append(curr_message)
            curr_message = PocsagMessage(codeword)

        # end of message
        elif in_message is True and isinstance(codeword, PocsagIdleFrame):
            # NOTE: might have to append copy not curr_message directly
            in_message = False
            messages.append(curr_message)
            curr_message = None

        # add to the message
        elif in_message is True and isinstance(codeword, PocsagMessageWord):
            curr_message.add_payload(codeword)

    # read through message objs
    for message in messages:
        print "NEW MESSAGE"
        message.read_alphanum()


if __name__ == "__main__":
    main()
