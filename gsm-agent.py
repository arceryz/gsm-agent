#!/bin/python3

# GSM Agent is a special server side daemon that is meant to run in a
# continuous loop. It listens on cellular channels for incoming SMS. 
# Based on the message received, gsmagent can run commands on the server.
# The senders are field agents of the Aurelius group.

from atlib import *
from os import path
from time import sleep


class Log:
    """ Log to file. """
    fh = None

    def init(logfile):
        """ Initialize the logfile with given name. """
        fh = file(logfile + ".1", "w")

    def print(str):
        """ Print message to log file and console. """
        print(str)
        fh.write(str + "\n")

    def err(str):
        """ Write error string. """
        Log.print("ERROR: {:s}".format(str))


class Agentbase:
    """ Agent storage system. """
    def __init__(self, dbpath):
        self.db = {}
        self.number_db = {}

        if path.isfile(dbpath):
            self.dbfile = open(dbpath, "r+")
        else:
            Log.err("Opening agentbase file {:s}".format(dbpath))

    
    def enlist(self, username, nr):
        """ Register new agent. """
        if self.db.has_key(username):
            print("Registering duplicate agent -> skipping")
            return
        # Register in two databases: One for linking username -> user and the
        # other for linking number -> username.
        self.db[username] = [ nr ]
        self.number_db[nr] = username


    def delist(self, username):
        """ Remove the agent from the database. """
        if not self.has_agent(username): return
        # Pop both the number and username db entries.
        self.number_db.pop(self.query(username)[0])
        self.db.pop(username)

    
    def query_username(self, number):
        """ Return username corresponding to agent. """
        return self.number_db[number]


    def query(self, username):
        """ Return agent. """
        return self.db[username]


class Comms:
    """ Manages communication with agents linked to database."""

    def __init__(self, serialpath, agentbase)
        if not path.exists(serialpath):
            Log.err("Opening serial device")
            return
        self.gsm = GSM_Device(serialpath) 
        self.agentbase = agentbase

    
    def poll(self):
        """ Poll all communication channels for incoming operations. 
        Return a list of commands and users that issue them."""
        cmdlist = []
        ops = self.gsm.receive_sms(SMS_Group.UNREAD)
        for msg in ops:
            nr = msg[0]
            op = msg[3]
            usr = self.agentbase.query_username(nr)
            cmdlist.append([ usr, op ])
        return cmdlist


class Executioner:
    """ Manages execution of commands and checking whether user is privileged
    to run a certain command. """
    def __init(self):
        pass


    def is_privileged(self, usr, cmd):
        """ Return True if user has authority to run command. """
        return True


    def execute(self, usr, cmd):
        """ Execute command if user has priviles to execute said command."""
        if not self.is_privileged(usr, cmd):
            Log.print("User {:s} is not privileged to run {:s}".format(usr,cmd))
        Log.print("User {:s} executing \"{:s}\"".format(usr, cmd))


class GSM_Agent:
    """ Core class that manages all component classes and is in
    control of the entire program. """

    def __init__(self, serialpath, dbpath):
        self.digest = []
        self.agentbase = Agentbase(dbpath)
        self.comms = Comms(serialpath, self.agentbase)
        self.exec = Executioner()


    def start(self, interval=30):
        """ Use the thread to run the GSM_Agent forever. """
        while True:
            sleep(interval)    
            cmdlist = self.comms.poll()
            for cmd in cmdlist: 
                self.exec.execute(cmd[0], cmd[1])
        pass
