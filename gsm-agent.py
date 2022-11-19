#!/bin/python3

# GSM Agent is a special server side daemon that is meant to run in a
# continuous loop. It listens on cellular channels for incoming SMS. 
# Based on the message received, gsmagent can run commands on the server.
# The senders are field agents of the Aurelius group.

from atlib import *
from core import *
from os import path
from time import sleep


# This is the device from which to listen.
gsm = GSM_Device("/dev/serial0")
auth = Auth("users", "auth")
poll_interval = 5.0


# Poll incoming messages and pass them to the request parser.
print("GSM Agent listening on PHONE")
while True:
    requests = gsm.receive_sms(SMS_Group.ALL)
    for req in requests:
        parse_request(req, auth, gsm)
    # Clear requests.
    gsm.delete_read_sms()
    sleep(poll_interval)
