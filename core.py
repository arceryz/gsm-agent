# Core GSM-agent library.
# Contains all the necessary components of gsm-agent.
from atlib import *
from configparser import ConfigParser
import subprocess


def read_csv(path):
    # Reads a CSV format file where each line is an entry and every comma
    # seperated entry is an element of the array.
    lines = []
    file = open(path, "r")
    while True:
        line = file.readline().replace(" ", "").replace("\n", "").split(",")
        if len(line) > 1:
            lines.append(line)
        else:
            break
    file.close()
    return lines


class Config:
    """ Class that loads the daemon parameters from a config file. """

    def __init__(self):
        self.poll_interval = 5.0
        self.serial_port = "/dev/serial0"
        self.users_file = "users"
        self.auth_file = "auth"


    def load_standard(self):
        """ Load configuration from standard path. """
        self.load("/etc/gsm-agent/gsm-agent.ini")
        return self


    def load(self, path):
        """ Load file from path. """
        print("Loading config file from {:s}".format(path))
        cfg = ConfigParser()
        cfg.read(path)
        self.poll_interval = float(cfg["Agent"]["poll_interval"])
        self.serial_port = cfg["Agent"]["serial_port"]
        self.users_file = cfg["Agent"]["users_file"]
        self.auth_file = cfg["Agent"]["auth_file"]
        return self


class Auth:
    # This class manages the database number -> user and user -> account.
    # Furthermore it manages the database of command clearance levels.
    def __init__(self, userfile, authfile):
        self.db = {}
        self.userdb = {}
        self.authdb = {}
        self.read_users(userfile)
        self.read_auth(authfile)


    def read_auth(self, file):
        print("Reading command database from {:s}".format(file))
        data = read_csv(file)
        for line in data:
            self.authdb[line[0]] = int(line[1])
            print("Cmd: {:10s} {:3d}".format(line[0], int(line[1])))


    def read_users(self, file):
        print("Reading user database from {:s}".format(file))
        data = read_csv(file)
        for line in data:
            self.register(line[0], line[1], line[2])


    def register(self, user, nr, clearance):
        # Register a user to the database.
        self.db[user] = [nr, int(clearance)]
        self.userdb[nr] = user
        print("Agent: {:10s} {:16s} {:3d}".format(user, nr, int(clearance)))


    def get_username(self, nr):
        user = self.userdb.get(nr)
        if user != None:
            return user
        return "unknown"


    # Call this method when you want to authorize a user for a certain command.
    def is_authorized(self, user, cmd):
        if not user in self.db or not cmd in self.authdb:
            return False
        clearance = self.db.get(user)[1]
        level = self.authdb.get(cmd)
        return clearance >= level


def parse_request(req, auth: Auth, gsm: GSM_Device):
    nr = req[0]
    args = req[-1].split(" ")
    cmd = args[0]

    # Verify authority.
    user = auth.get_username(nr)
    print("Request from {:s} ({:s}) -> {:s}".format(user, nr, req[-1]))

    if auth.is_authorized(user, cmd):
        # Execute the command and send results back.
        finalargs = [ "./scripts/{:s}".format(cmd) ] + args[1:]
        print("Executing {:s}".format(str(finalargs)))
        result = subprocess.run(finalargs, capture_output=True)
        output = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
        gsm.send_sms(nr, output)
