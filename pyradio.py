#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PyRadio: Curses based Internet Radio Player
# http://www.coderholic.com/pyradio
# Ben Dowling - 2009 - 2010

import os
import sys
import curses
import thread
import random
import subprocess

def rel(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)

class Log(object):
    """ Log class that outputs text to a curses screen """

    msg = None
    cursesScreen = None

    def __init__(self):
        pass

    def setScreen(self, cursesScreen):
        self.cursesScreen = cursesScreen
        self.width = cursesScreen.getmaxyx()[1] - 5

        # Redisplay the last message
        if self.msg:
            self.write(self.msg)

    def write(self, msg):
        self.msg = msg.strip()

        if self.cursesScreen:
            self.cursesScreen.erase()
            self.cursesScreen.addstr(0, 1, self.msg[0: self.width].replace("\r", "").replace("\n", ""))
            self.cursesScreen.refresh()

    def readline(self):
        pass

class Player(object):
    """ Media player class. Playing is handled by mplayer """
    process = None

    def __init__(self, outputStream):
        self.outputStream = outputStream
        opts = ["mplayer", "-slave", "-input", "file=/tmp/pyradio-remote"]
        os.system("mkfifo /tmp/pyradio-remote")

    def __del__(self):
        self.close()

    def updateStatus(self):
        try:
            user_input = self.process.stdout.readline()
            while(user_input != ''):
                self.outputStream.write(user_input)
                user_input = self.process.stdout.readline()
        except:
            pass

    def is_playing(self):
        return bool(self.process)

    def play(self, stream_url):
        """ use mplayer to play a stream """
        self.close()
        if stream_url.split("?")[0][-3:] in ['m3u', 'pls']:
            opts = ["mplayer", "-quiet", "-slave", "-input", "file=/tmp/pyradio-remote","-idle","-playlist", stream_url]
        else:
            opts = ["mplayer", "-quiet", "-slave", "-inpu", "file=/tmp/pyradio-remote","-idle", stream_url]
        self.process = subprocess.Popen(opts, shell=False,
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

        thread.start_new_thread(self.updateStatus, ())



    def sendCommand(self, command):
        """ send keystroke command to mplayer """
        if(self.process != None):
            try:
                os.system("echo "+ command +" > /tmp/pyradio-remote &")

            except:
                pass

    def mute(self):
        """ mute mplayer """
        self.sendCommand("mute")

    def pause(self):
        """ pause streaming (if possible) """
        self.sendCommand("pause")

    def close(self):
        """ exit pyradio (and kill mplayer instance) """
        self.sendCommand("q")
        if self.process != None:
            os.kill(self.process.pid, 15)
            self.process.wait()
        self.process = None

    def volumeUp(self):
        """ increase mplayer's volume """
        self.sendCommand("volume 70") # when I test it, :up goes down and 70 goes up by 3%…

    def volumeDown(self):
        """ decrease mplayer's volume """
        self.sendCommand("volume :down")

class PyRadio(object):
    startPos = 0
    selection = 0
    playing = -1

    def __init__(self, stations):
        self.stations = stations

    def setup(self, stdscr):
        self.stdscr = stdscr

        try:
            curses.curs_set(0)
        except:
            pass

        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(8, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_GREEN)

        self.log = Log()
        self.player = Player(self.log)

        self.stdscr.nodelay(0)
        self.setupAndDrawScreen()

        self.run()


    def setupAndDrawScreen(self):
        self.maxY, self.maxX = self.stdscr.getmaxyx()

        self.headWin = curses.newwin(1, self.maxX, 0, 0)
        self.bodyWin = curses.newwin(self.maxY-2, self.maxX, 1, 0)
        self.footerWin = curses.newwin(1, self.maxX, self.maxY-1, 0)
        self.initHead()
        self.initBody()
        self.initFooter()

        self.log.setScreen(self.footerWin)

        #self.stdscr.timeout(100)
        self.bodyWin.keypad(1)

        #self.stdscr.noutrefresh()

        curses.doupdate()

    def initHead(self):
        info = " PyRadio 0.2 "
        self.headWin.addstr(0, 0, info, curses.color_pair(4))
        rightStr = "www.coderholic.com/pyradio"
        self.headWin.addstr(0, self.maxX - len(rightStr) - 1, rightStr,
                            curses.color_pair(2))
        self.headWin.bkgd(' ', curses.color_pair(7))
        self.headWin.noutrefresh()

    def initBody(self):
        """ Initializes the body/story window """
        #self.bodyWin.timeout(100)
        #self.bodyWin.keypad(1)
        self.bodyMaxY, self.bodyMaxX = self.bodyWin.getmaxyx()
        self.bodyWin.noutrefresh()
        self.refreshBody()

    def initFooter(self):
        """ Initializes the body/story window """
        self.footerWin.bkgd(' ', curses.color_pair(7))
        self.footerWin.noutrefresh()

    def refreshBody(self):
        self.bodyWin.erase()
        self.bodyWin.box()

        self.bodyWin.move(1, 1)
        maxDisplay = self.bodyMaxY - 1
        for idx in range(maxDisplay - 1):
            if(idx > maxDisplay):
                break
            try:
                station = self.stations[idx + self.startPos]
                col = curses.color_pair(5)

                if idx + self.startPos == self.selection and \
                   self.selection == self.playing:
                    col = curses.color_pair(9)
                    self.bodyWin.hline(idx + 1, 1, ' ', self.bodyMaxX - 2, col)
                elif idx + self.startPos == self.selection:
                    col = curses.color_pair(6)
                    self.bodyWin.hline(idx + 1, 1, ' ', self.bodyMaxX - 2, col)
                elif idx + self.startPos == self.playing:
                    col = curses.color_pair(4)
                    self.bodyWin.hline(idx + 1, 1, ' ', self.bodyMaxX - 2, col)
                self.bodyWin.addstr(idx + 1, 1, station[0], col)

            except IndexError:
                break

        self.bodyWin.refresh()

    def run(self):
        while True:
            try:
                c = self.bodyWin.getch()
                ret = self.keypress(c)
                if (ret == -1):
                    return
            except KeyboardInterrupt:
                break

    def setStation(self, number):
        """ Select the given station number """
        number = max(0, number)
        number = min(number, len(self.stations) - 1)

        self.selection = number

        maxDisplayedItems = self.bodyMaxY - 2

        if self.selection - self.startPos >= maxDisplayedItems:
            self.startPos = self.selection - maxDisplayedItems + 1
        elif self.selection < self.startPos:
            self.startPos = self.selection

    def playSelection(self):
        self.playing = self.selection
        name = self.stations[self.selection][0]
        stream_url = self.stations[self.selection][1].strip()
        self.log.write('Playing ' + name)
        try:
            self.player.play(stream_url)
        except OSError, e:
            self.log.write('Error starting player.' \
                           'Are you sure mplayer is installed?')


    def keypress(self, char):
        # Number of stations to change with the page up/down keys
        pageChange = 5
        # Maximum number of stations that fit on the screen at once
        maxDisplayedItems = self.bodyMaxY - 2

        if char == curses.KEY_EXIT or char == ord('q'):
            self.player.close()
            return -1
        elif char in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            self.playSelection()
            self.refreshBody()
            return
        elif char == ord(' '):
            if self.player.is_playing():
                self.player.close()
                self.log.write('Playback stopped')
            else:
                self.playSelection()
            self.refreshBody()
            return
        elif char == curses.KEY_DOWN or char == ord('j'):
            self.setStation(self.selection + 1)
            self.refreshBody()
            return
        elif char == curses.KEY_UP or char == ord('k'):
            self.setStation(self.selection - 1)
            self.refreshBody()
            return
        elif char == ord('+'):
            self.player.volumeUp()
            return
        elif char == ord('-'):
            self.player.volumeDown()
            return
        elif char == curses.KEY_PPAGE:
            self.setStation(self.selection - pageChange)
            self.refreshBody()
            return
        elif char == curses.KEY_NPAGE:
            self.setStation(self.selection + pageChange)
            self.refreshBody()
            return
        elif char == ord('m'):
            self.player.mute()
            return
        elif char == ord('r'):
            # Pick a random radio station
            self.setStation(random.randint(0, len(self.stations)))
            self.playSelection()
            self.refreshBody()
        elif char == ord('#') or char == curses.KEY_RESIZE:
            self.setupAndDrawScreen()
            #self.refreshBody()

        elif char == curses.KEY_HOME:
            self.setStation(0)
            self.refreshBody()

        elif char == curses.KEY_END:
            self.setStation(10000) # big number, just in case
            self.refreshBody()

        # à-la emacs
        elif char == ord('n'):
            self.setStation(self.selection + 1)
            self.refreshBody()

        elif char == ord('p'):
            self.setStation(self.selection - 1)
            self.refreshBody()


if __name__ == "__main__":
    # Default stations list
    stations = [
        ("Stoner rock Eule", "http://yp.shoutcast.com/sbin/tunein-station.pls?id=104308"),
        ("campusgrenoble", "http://live.campusgrenoble.org:9000/rcg112.m3u"),


        ("Digitally Imported: Chillout", "http://di.fm/mp3/chillout.pls"),
        ("Digitally Imported: Trance", "http://di.fm/mp3/trance.pls"),
        ("Digitally Imported: Classic Techno",
         "http://di.fm/mp3/classictechno.pls"),
        ("Frequence 3 (Pop)", "http://streams.frequence3.net/hd-mp3.m3u"),
        ("Mostly Classical", "http://www.sky.fm/mp3/classical.pls"),
        ("Ragga Kings", "http://www.raggakings.net/listen.m3u"),
        ("Secret Agent (Downtempo)", "http://somafm.com/secretagent.pls"),
        ("Slay Radio (C64 Remix)", "http://sc.slayradio.org:8000/listen.pls"),
        ("SomaFM: Groove Salad",
         "http://somafm.com/startstream=groovesalad.pls"),
        ("SomaFM: Beat Blender",
         "http://somafm.com/startstream=beatblender.pls"),
        ("SomaFM: Cliq Hop", "http://somafm.com/startstream=cliqhop.pls"),
        ("SomaFM: Sonic Universe",
         "http://somafm.com/startstream=sonicuniverse.pls"),
        ("SomaFM: Tags Trance Trip", "http://somafm.com/tagstrance.pls"),
    ]
    csvFile = os.path.join(os.path.expanduser("~/.pyradio"), "stations.csv")
    if len(sys.argv) > 1 and sys.argv[1]:
        csvFile = sys.argv[1]

    try:
        csv = open(csvFile, "r")
        stations = []
        for line in csv.readlines():
            line = line.strip()
            if not line:
                continue
            try:
                (name, url) = line.split(",")
                stations.append((name, url))
            except:
                print "Error, skipping ", line
    except IOError:
        print "Could not open stations file '%s'. " \
              "Using default stations list" % csvFile

    pyRadio = PyRadio(stations)
    curses.wrapper(pyRadio.setup)
