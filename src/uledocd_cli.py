#!/usr/bin/env python3

# Unofficial LED OCD - Open-source cross-platform configuration
# software for Comet Pinball's amazing LED OCD board.
# Copyright (C) 2026  Stephen Jonke

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import platform
import argparse
from serial.tools import list_ports

from uledocd import ULEDOCD, Manufacturers


def	ProcessCmd(cmd, cmd_args, led_ocd):
    cmd = cmd.upper()
    if cmd == "VERSION":
        result = led_ocd.SendVersionCmd()[1]
        if result:
            print(result)
        else:
            print("Error: VERSION command didn't work")
    elif cmd == "READSETTINGS":
        result = led_ocd.SendReadSettingsCmd()[1]
        if result:
            for x in result:
                print(x)
        else:
            print("Error: READSETTINGS command didn't work")
    elif cmd == "SAVESETTINGS":
        result = led_ocd.SendSaveSettingsCmd()
        if not result:
            print("Error: SENDSETTINGS comamnd didn't work")
    elif cmd == "NORMALOCD":
        result = led_ocd.SendNormalOCDCmd()
        if not result:
            print("Error: NORMALOCD comamnd didn't work")
    elif cmd == "MANUAL":
        result = led_ocd.SendManualCmd()
        if not result:
            print("Error: MANUAL comamnd didn't work")
    elif cmd == "NORMALOCD":
        result = led_ocd.SendPassthroughCmd()
        if not result:
            print("Error: PASSTHROUGH comamnd didn't work")
    elif cmd == "SETPN":
        result = led_ocd.SendSetPNCmd(int(cmd_args[0]), cmd_args[1])
        if not result:
            print("Error: SETPN comamnd didn't work")
    elif cmd == "SETPB":
        result = led_ocd.SendSetPBCmd(int(cmd_args[0]), int(cmd_args[1]), int(cmd_args[2]))
        if not result:
            print("Error: SETPB comamnd didn't work")
    elif cmd == "SETPD":
        result = led_ocd.SendSetPDCmd(int(cmd_args[0]), int(cmd_args[1]))
        if not result:
            print("Error: SETPD comamnd didn't work")
    elif cmd == "SETLP":
        result = led_ocd.SendSetLPCmd(int(cmd_args[0]), int(cmd_args[1]))
        if not result:
            print("Error: SETLP comamnd didn't work")
    elif cmd == "SETLB":
        result = led_ocd.SendSetLBCmd(int(cmd_args[0]), int(cmd_args[1]))
        if not result:
            print("Error: SETLB comamnd didn't work")
    elif cmd == "CHECK":
        result = led_ocd.SendCheckCmd()
        if not result:
            print("Error: CHECK comamnd didn't work")
    else:
        print(f"ERROR: Invalid command. Command: {cmd}, Args: {cmd_args}")



def uledocd_cli():        
    parser = argparse.ArgumentParser(description="Command-Line interface for the led_ocd and gi_ocd boards",
                                    usage="uledocd_cli [-h|--help] [-p|--port TTY] [-m|--manufacturer MANUFACTURER] [-c|--command COMMAND]",
                                    epilog="Example: uledocd_cli -p /dev/ttyUSB3 -m CAPCOMA -c SETLP=11,3")
    
    parser.add_argument("-p", "--port", dest="tty", type=str, help="port name for LED OCD interface (if not provided it will try to auto-select)")
    
    parser.add_argument("-c", "--command",
                        default="VERSION",
                        # choices=["VERSION", "READSETTINGS", "SETPN", "SETPB", "SETPD", "SETLP", "SETLB", "SAVESETTINGS", "NORMALOCD", "MANUAL", "PASSTHROUGH", "CHECK"],
                        type=str,
                        help="Set the command to send (default VERSION). Valid commands: VERSION; READSETTINGS; SETPN=Profile,Name; SETPB=Profile,BrightnessNum,Value; SETPD=Profile,Delay; SETLP=Lamp,Profile; SETLB=Lamp,Profile; SAVESETTINGS; NORMALOCD; MANUAL; PASSTHROUGH; CHECK")
    
    parser.add_argument("-m", "--manufacturer", dest="manuf",
                        choices=["WPC", "STERN", "CAPCOMA", "CAPCOMB"],
                        type=str,
                        help="set the game manufacturer (if not provided it will attempt to detect the platform)")
    
    args = parser.parse_args()

    cmd_parts = args.command.split("=", maxsplit=1)
    cmd = cmd_parts[0].upper()
    if len(cmd_parts) > 1:
        cmd_args = cmd_parts[1].split(",")
    else:
        cmd_args = []
        
    num_args = len(cmd_args)
    
    # print("Command: ", cmd, " Args: ", cmd_args if len(cmd_parts) > 1 else "None")
    
    valid_cmds = ["VERSION", "READSETTINGS", "SAVESETTINGS", "NORMALOCD", "MANUAL", "PASSTHROUGH", "CHECK", "SETPN", "SETPB", "SETPD", "SETLP", "SETLB"]
    valid_args = {
        "VERSION": 0,
        "READSETTINGS": 0,
        "SAVESETTINGS": 0,
        "NORMALOCD": 0,
        "MANUAL": 0,
        "PASSTHROUGH": 0,
        "CHECK": 0,
        "SETPN": 2,
        "SETPB": 3,
        "SETPD": 2,
        "SETLP": 2,
        "SETLB": 2
    }
        
    if any(cmd in x for x in valid_cmds) and (num_args == valid_args[cmd]):
        if args.tty:
            tty = args.tty
        else:
            # port_choices = list_ports.grep(".*(tty\\.usbserial|ttyUSB[0-9]|COM[0-9]).*")
            port_choices = list_ports.comports()
            port_list = []

            for x in port_choices:
                port_list.append(x[0])

            num_ports = len(port_list)

            if num_ports >= 1:
                # It's usually the last port option
                tty = port_list[-1]
            else:
                plat = platform.system().lower()
                if plat == "darwin":
                    tty = "/dev/tty.usbserial-AG0KPUS5"
                elif plat == "linux":
                    tty = "/dev/ttyUSB0"
                elif plat == "windows":
                    tty = "COM3"
                else:
                    tty = "/dev/ttyUSB0"

        if args.manuf:
            mdict = {
                "WPC": Manufacturers.WPC,
                "STERN": Manufacturers.STERN,
                "CAPCOMA": Manufacturers.CAPCOMA,
                "CAPCOMB": Manufacturers.CAPCOMB
            }
            manuf = args.manuf.upper()
            manu_id = mdict[manuf]
        else:
            manu_id = None

        led_ocd = ULEDOCD(tty_port=tty, manufacturer=manu_id)
        ProcessCmd(cmd, cmd_args, led_ocd)
            
    else:
        print(f"ERROR: Invalid command or number of arguments. Command: {cmd}, Args: {cmd_args}")
        print(f"Valid number of arguments for {cmd}: {valid_args[cmd]}")
    

if __name__ == "__main__":
    uledocd_cli()
