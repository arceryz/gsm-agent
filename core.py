# Core GSM-agent library.
# Contains all the necessary components of gsm-agent.
from atlib import *
from configparser import ConfigParser
import subprocess
import csv


class Config:
    """ Class that loads the daemon parameters from a config file. """

    def __init__(self):
        self.poll_interval = 5.0
        self.server_phone_number = "+???????????"
        self.conf_file = ""
        self.serial_port = "/dev/serial0"
        self.users_file = "/usr/share/gsm-agent/users"
        self.scripts_path = "/usr/share/gsm-agent/scripts"
        self.commands = {}


    def load_standard(self):
        """ Load configuration from standard path. """
        paths = [
            "/etc/gsm-agent/gsm-agent.ini",
            "/etc/gsm-agent/gsm-agent.conf"
        ]
        for p in paths:
            if self.load(p) != None:
                return self 
        return None


    def load(self, path):
        """ Load file from path. """
        print("Loading config file from {:s}".format(path))
        cfg = ConfigParser()
        cfg.read(path)
        if not cfg.has_section("Agent"):
            print("Error loading config from {:s}, \
                    no [Agent] section or invalid path.".format(path))
            return None

        # Load parameters.
        self.conf_file = path
        self.server_phone_number = cfg["Agent"]["server_phone_number"]
        self.poll_interval = float(cfg["Agent"]["poll_interval"])
        self.serial_port = cfg["Agent"]["serial_port"]
        self.users_file = cfg["Agent"]["users_file"]
        self.scripts_path = cfg["Agent"]["scripts_path"]
        self.commands = dict(cfg["Commands"])

        print(self)
        return self


    def __str__(self):
        s =  "conf_file           = {:s}\n".format(self.conf_file)
        s += "server_phone_number = {:s}\n".format(self.server_phone_number)
        s += "poll_interval       = {:.1f}\n".format(self.poll_interval)
        s += "serial_port         = {:s}\n".format(self.serial_port)
        s += "users_file          = {:s}\n".format(self.users_file)
        s += "scripts_path        = {:s}\n".format(self.scripts_path)
        for c in self.commands:
            s += "+Cmd n={:10s} g={:s}\n".format(c, str(self.commands[c]))
        return s


    def get_command_group(self, cmd):
        if cmd not in self.commands:
            return ""
        return self.commands[cmd]


class UserDB:
    # This class manages the database number -> user and user -> account.
    # Furthermore it manages the database of command clearance levels.
    def __init__(self):
        self.user_db = {}
        self.number_db = {}


    def load(self, file):
        """ Load user database from file. """
        print("Loading user database from {:s}".format(file))
        reader = csv.reader(open(file), delimiter=";")
        for u in reader:
            self.add_user(u[0].strip(), u[1].strip(), u[2].strip().split(" "))
        print("")
        return self


    def add_user(self, user, nr, groups):
        """ Register a new user. """
        self.user_db[user] = [nr, groups]
        self.number_db[nr] = user
        print("+Agent u={:10s} nr={:16s} g={:s}".format(user, nr, str(groups)))


    def get_username(self, nr):
        """ Get username from number. """
        if nr in self.number_db:
            return self.number_db[nr]
        return "unknown"


    def get_groups(self, user):
        """ Return users groups. """
        if user in self.user_db:
            return self.user_db[user][1]
        return []


def parse_request(req, gsm: GSM_Device, userdb: UserDB, conf: Config):
    nr = req[0]
    args = req[-1].split(" ")
    cmd = args[0]

    # Get user's groups and verify authority.
    user = userdb.get_username(nr)
    groups = userdb.get_groups(user)
    cmd_group = conf.get_command_group(cmd)
    print("Request from {:s} ({:s}) -> {:s}".format(user, nr, req[-1]))

    if cmd_group in groups:
        # Execute the command and send results back.
        args[0] = "{:s}/{:s}".format(conf.scripts_path, cmd)
        print("Authorized -> Executing {:s}".format(str(args)))
        result = subprocess.run(args, capture_output=True)
        output = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")

        # Reply to the request.
        gsm.send_sms(nr, output)
    else:
        print("Rejected -> Insufficient privileges: {:s} required, have {:s}"
              .format(cmd_group, str(groups)))
