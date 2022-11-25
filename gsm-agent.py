#!/bin/python3

# GSM Agent is a special server side daemon that is meant to run in a
# continuous loop. It listens on cellular channels for incoming SMS. 
# Based on the message received, gsmagent can run commands on the server.
# The senders are field agents of the Aurelius group.

from atlib import *
from core import *
from time import sleep


# Load the configuration.
print("GSM Agent loading")
conf = Config().load_standard()
if conf == None:
    print("Invalid config file -> Aborting")
userdb = UserDB().load(conf.users_file)
gsm = GSM_Device(conf.serial_port)

# Poll incoming messages and pass them to the request parser.
print("GSM Agent listening on PHONE")
while True:
    requests = gsm.receive_sms(SMS_Group.ALL)
    for req in requests:
        parse_request(req, gsm, userdb, conf)

    # Clear requests.
    for i in range(3):
        print(gsm.delete_read_sms())
    sleep(conf.poll_interval)
