# gsm-agent
Linux daemon that allows a set of shell scripts to be executed on the server and echoed back via
SMS. Supports authority-level checking and users/usernames for security.

# How to use

Give this daemon a working directory (/usr/share/gsm-agent) and put two files in there:
- `users` file csv in format `user, phonenumber, authoritylevel` where authority
level is an integer that grants the user privilige to run certain commands.
Add a user `unknown` for the privileges of unregistered users.

- `auth` file csv in format `command, authoritylevel` which tells which commands are allowed to be run
under which minimum authoritylevel. E.g, an authority of 0 tells that anyone can run this command.

- Put the scripts you want to run remotely the `/scripts` subdirectory (you can change this).

These files are currently hard-coded in the python. You can edit [gsm-agent.py](gsm-agent.py) to change
the filenames if you want. By default, the `unknown` user is used as fallback if no user is present,
make sure to add this entry to your users file.

The way that this daemon works is 
1. Receive SMS messages on the SIM800L chip connected on `/dev/serial0`.
The SMS messages should be formatted as `[command] args...` as a normal linux command.
2. The server checks if the sending phonenumber is a registered user, if so uses that users
authority level, otherwise falls back to the authority of `unknown` user.
3. If `authority > minauthority` of the command, then the command is executed and output is captured.
4. The command stdout+stderr is echoed back to the sender as an SMS message. Make sure you have enough
prepaid on your SIM card.
5. The user receives the output.

By default, the polling interval for new messages is set to 10 seconds. So be aware that the
response time depends on this. Setting it to 1 minute is too extreme, since then the user might
have to wait for up to a minute.

# Installation

This library builds upon my SMS/GSM library [ATLib](https://github.com/swordstrike1/ATlib).
The library must be installed on your machine or in the working directory of the daemon.
You can simply run the daemon using python. Be aware that the serial port needs to be accessed,
so add the daemon user to the `dialout` group (Debian).

You can create a systemd service script for the daemon to make it run automatically:
```conf
[Unit]
Description=GSM Agent Server

[Service]
Type=simple
User=gsm-agent
WorkingDirectory=/usr/share/gsm-agent
ExecStart=python -u /usr/share/gsm-agent/gsm-agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```
