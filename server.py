
import sys
import socket
import argparse
from threading import Thread, Event
from getch import getch
from time import sleep

MESSAGE = "Hello, World!"

""" Message protocol

    (x[7] . x[0:7]) . yyyyzzzzzzzzzzzzzzzzz

    x - packet type
    y - size of data segment
    z - message data

    Possible packet types (x[7])::
        0: Request
        1: Response

    Possible packet types (x[0:7])::
        0: Heartbeat
        2: Screen data
"""

try:
    input = raw_input
except:
    pass

class Server(object):
    def __init__(self, dest_ip, send_port, recv_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest_ip = dest_ip
        self.send_port = send_port
        self.recv_port = recv_port
        self.sock.bind((dest_ip, send_port))
        self.sock.settimeout(0.1)

        self.dest_terminal_size = (100, 100)
        self.last_display = ""
        self.event_stop = Event()

    """ 0 - HEARTBEAT """
    def req_heartbeat(self):
        x = 0x00 | 0
        y = 6
        z = "alive?"

        self.send_raw(pack(x, y, z))

    def resp_heartbeat(self):
        x = 0x80 | 0
        y = 12
        z = "yeah my dude"

        self.send_raw(pack(x, y, z))

    """ 2 - DISPLAY """
    def req_display(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        x = 0x80 | 2
        y = 4
        z = ("%x" % rows).zfill(2) + ("%x" % cols).zfill(2)

        self.send_raw(pack(x, y, z))

    def resp_display(self):
        x = 0x80 | 2
        rows, cols = self.dest_terminal_size

        z = self._dummy_display_data(rows, cols)
        y = len(z)

        self.send_raw(pack(x, y, z))

    def _dummy_display_data(self, rows, cols):
        """ Return dummy display data """
        s = ""
        s += "A" * cols + "\n"
        for _ in range(rows - 2):
            s += "B" + " " * (cols - 2) + "C" + "\n"
        s += "D" * cols + "\n"
        return s

    """ Helper functions """
    def pack(self, x, y, z):
        """ Make packet """
        assert x <= 0xFF
        assert y <= 0xFFFFFFFF
        assert y == len(z)

        x_ = ("%x" % x).zfill(2)
        y_ = ("%x" % y).zfill(8)
        z_ = z

        return x_ + y_ + z_

    """ RAW SEND """
    def send_raw(self, packet):
        self.sock.sendto(packet, (self.dest_ip, self.send_port))

    def recv_raw(self, size=1024):
        data, addr = self.sock.recvfrom(size)
        if addr == self.dest_ip:
            print(data)

    """ Actual processing n stuff """
    def handle_recv(self):
        try:
            packet_header = self.recv_raw(5)

            # Unpack
            x = chr(packet_header[0])
            y = long(packet_header[1:5])
            z = self.recv_raw(y)

            # Handle packet
            if x == 0x00 | 0:
                # Heartbeat request
                self.resp_heartbeat()
            elif x == 0x80 | 0:
                # Heartbeat response
                print("[INFO] Heartbeat response received")
            elif x == 0x00 | 2:
                # Display request
                rows = long(z[0:2])
                cols = long(z[2:4])
                self.dest_terminal_size = (rows, cols)

                self.resp_display()
            elif x == 0x80 | 2:
                # Display response
                self.last_display = z
        except socket.timeout:
            pass

    def update_loop(self):
        """ Handles incoming packets and updates display """
        while not self.event_stop.is_set():
            self.handle_recv()
            self.req_display()
            sleep(0.01)

    def input_loop(self):
        while not self.event_stop.is_set():
            c = getch()
            if c == "q":
                print("Quitting")
                self.event_stop.set()

    def display_loop(self):
        while not self.event_stop.is_set():
            print(self.last_display)
            sleep(0.001)

    def run(self):
        """ Run the server """
        threads = []
        threads.append(Thread(target=self.update_loop))
        threads.append(Thread(target=self.input_loop))
        threads.append(Thread(target=self.display_loop))

        for t in threads:
            t.daemon = True  # Set all threads as daemon
            t.start()

        try:
            while not self.event_stop.is_set():
                sleep(0.001)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ASCII Skype!")
    parser.add_argument("--dest", "-d",
                        help="Destination IP")
    parser.add_argument("--recv_port", "-r",
                        help="Receive Port")
    parser.add_argument("--send_port", "-s",
                        help="Send Port")

    args = parser.parse_args()

    if not args.dest or not args.send_port or not args.recv_port:
        parser.print_help()
        sys.exit(1)

    s = Server(args.dest, int(args.send_port), int(args.recv_port))
    s.run()
