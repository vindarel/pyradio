#!/usr/bin/env python

# PyRadio: Curses based Internet Radio Player
# http://www.coderholic.com/pyradio
# Ben Dowling - 2009 - 2010
# Vincent Dardel 2012


import os
import sys


if __name__ == '__main__':
    # from optparse import OptionParser

    # parser = OptionParser()
    # parser.add_option("-p", "--pause", # command="pause",
    #                   help="pause pyradio") #, metavar="FILE")
    # # parser.add_option("-q", "--quiet",
    # #                   action="store_false", dest="verbose", default=True,
    # #                   help="don't print status messages to stdout")

    # (options, args) = parser.parse_args()


    os.system("echo "+sys.argv[1]+" > /tmp/pyradio-remote &")
