
""" Module renders the UI """

import sys
import argparse
from server import Server
import os
from time import sleep
from random import choice
import string

class Ui(object):
    def __init__(self, *args):
        self.server = Server(*args)

        self.display_size_per = 0.8

    def run(self):
        while True:
            self.print_display()
            sleep(0.01)

    def print_display(self):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        # Draw borders
        rows, cols = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        cols = int(cols)

        s = ""
        s += "=" * cols + "\n"
        for _ in range(rows - 4):
            line = ""
            line += "|"

            # Add display section
            cols_display = int(float(cols - 2) * self.display_size_per)
            data_display = " " * 5 + \
                "".join(choice(string.ascii_uppercase) for _ in range(cols_display - 10)) + \
                " " * 5

            line += data_display.ljust(cols_display, " ")
            line += "|"

            # Add commands
            line += " [INFO] TEST MESSAGE"

            # Fill rest of screen
            line = line.ljust(cols - 1, " ")
            line += "|"

            # Add line to screen buffer
            s += line + "\n"
        s += "=" * cols + "\n"

        # Print
        sys.stdout.flush()
        sys.stdout.write(s)

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

    ui = Ui(args.dest, int(args.send_port), int(args.recv_port))
    ui.run()
