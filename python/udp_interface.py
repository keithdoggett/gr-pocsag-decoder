"""
    Module with functions to read from UDP Sink in GNURadio
    Will take the bits from the UDP sink, flip them 
    (since the high freq in the 2-FSK is binary 0 and GNURadio sets that to 1),
    and return them as a string[] which can be added to buffer in pocsag_reader

    Will also implement array cleanup function in here since
    the buffer would grow infinitely large and the same
    data would be re-processed every loop

    TODO: look into just using a sizeable queue as data structure
"""
import socket


class UdpInterface(object):
    def __init__(self, addr, port, payload_size):
        self.addr = addr
        self.port = port
        self.payload_size = payload_size
        self.sock = self._make_conn()
        self.buffer = []

    def _make_conn(self):
        """
            make connection to the address and port specified
            set self.sock to bound socket
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.addr, self.port))
        print "connected to socket"
        return sock

    def read_socket(self):
        """
            read in data from socket to buffer
            will perform necessary bit flips here and make it
            a string instead of bytes
        """
        data, _ = self.sock.recvfrom(self.payload_size)
        data = bytearray(data)

        for i in data:
            bit = i ^ 1
            self.buffer.append(str(bit))

    def clean_buffer(self, last_idx):
        """
            remove data that is no longer useful in the buffer
            will create a new buffer from curr_buffer[last_idx:]

            may perform other actions eventually
        """
        # prev_len = len(self.buffer)
        self.buffer = self.buffer[last_idx:]

        # print "clean_buffer info", prev_len, len(self.buffer), last_idx
