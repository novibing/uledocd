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

import serial
from tkinter import *
import json
from packets import Watchdog, LampProfile, ProfileName, ProfileBrightnessPercent, ProfileDelay


class ParseCode:
    OPENBRACKET = 123
    CLOSEBRACKET = 125
    VERSION = 86
    GUIVERSION = 71
    ZEROCHAR = 48
    BCHAR = 66
    DCHAR = 68
    GCHAR = 71
    LCHAR = 76
    NCHAR = 78
    PCHAR = 80
    VCHAR = 86
    WATCHDOG = 90

class Manufacturers:
    WPC = 0
    STERN = 1
    CAPCOMA = 2
    CAPCOMB = 3

SETTINGS_OBJ_CNT_WPC    = 144
SETTINGS_OBJ_CNT_STERN  = 160


class CustomULEDOCDEncoder(json.JSONEncoder):
    def default(self, obj):
        # Only return object if it has a to_dict method
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return


class CustomULEDOCDDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        cls = dct["class"].lower()
        if cls == "lampprofile":
            obj = LampProfile(lamp_num=dct["lamp_num"], profile_num = dct["profile_num"])
        elif cls == "profilename":
            obj = ProfileName(profile_num=dct["profile_num"], name=dct["name"])
        elif cls == "profiledelay":
            obj = ProfileDelay(profile_num=dct["profile_num"], delay=dct["delay"])
        elif cls == "profilesbrightnesspercent":
            obj = ProfileBrightnessPercent(profile_num=dct["profile_num"], brightness_num=dct["brightness_num"], percent=dct["percent"])
        # elif cls == "watchdog":
        #     obj = Watchdog(value=dct["value"])
        else:
            print(f"Unknown class: {cls}")
            return dct
        
        return obj


class ULEDOCD:
    def __init__(self, tty_port=None, manufacturer=None):
        self.tty_port = tty_port
        self.tty_serial = None
        self.settings = []

        if manufacturer != None:
            if manufacturer >= 0 and manufacturer <= 3:
                self.manufacturer = manufacturer
            else:
                self.manufacturer = Manufacturers.WPC
                print(f"Unknown manufacturer {manufacturer}. Defaulting to WPC. Manufacturer must be 0-3")
        else:
            self.manufacturer = Manufacturers.WPC


    def __repr__(self):
        map = {
            0:"WPC",
            1:"STERN",
            2:"CAPCOMA",
            3:"CAPCOMB"
        }

        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(tty_port=\"{self.tty_serial.name}\", manufacturer={"None" if self.manufacturer is None else f"{__class__.__module__}.Manufacturers."+map[self.manufacturer]})'
        return s


    def __del__(self):
        if self.tty_serial:
            self.Disconnect()


    def ToJSON(self):
        if self.ValidateSettings(self.settings):
            return json.dumps(self.settings, cls=CustomULEDOCDEncoder, indent=4, sort_keys=True)
        else:
            return False

    
    def FromJSON(self, json_filename):
        with open(json_filename, 'r') as f:
            data = f.readlines(-1)
        if data:
            json_data = "".join(data)
            new_settings = json.loads(json_data, cls=CustomULEDOCDDecoder)
            if self.ValidateSettings(new_settings):
                self.settings = None
                self.settings = new_settings
                return True
        return False


    def Disconnect(self):
        if self.tty_serial.is_open:
            self.tty_serial.close()


    def SetPort(self, tty_port):
        self.tty_port = tty_port


    def Connect(self):
        if self.tty_port:
            if self.tty_serial:
                if self.tty_serial.is_open:
                    self.Disconnect()
                    self.OpenPort(tty_port=self.tty_port)
                else:
                    self.OpenPort(tty_port=self.tty_port)
            else:
                self.tty_serial = serial.Serial(self.tty_port, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, timeout=2, write_timeout=2)

            print(f"Using \"{self.tty_serial.name}\" for LED OCD interface")


    def ParseMessage(self, message, start, length):
        match message[start + 1]:
            case ParseCode.WATCHDOG:  # this constant doesn't exist in ParseCode; fallback below
                if length == 6:
                    # return "WATCHDOG=%c%c%c" % (message[start + 2], message[start + 3], message[start + 4])
                    return Watchdog("%c%c%c" % (message[start + 2], message[start + 3], message[start + 4]))
            case ParseCode.VERSION:
                if length == 5:
                    version = (message[start + 2] - ParseCode.ZEROCHAR) * 10 + (message[start + 3] - ParseCode.ZEROCHAR)
                    return "LED OCD Firmware v%c%c" % (message[start + 2], message[start + 3])
            case ParseCode.GUIVERSION:
                if length == 5:
                    return "GI OCD Firmware v%c%c" % (message[start + 2], message[start + 3])
            case ParseCode.LCHAR:
                match message[start + 4]:
                    case ParseCode.PCHAR:
                        if length == 7:
                            if self.manufacturer == Manufacturers.STERN:
                                lamp_num = message[start + 3] * 8 + message[start + 2] + 1
                            else:
                                lamp_num = ((message[start + 2] + 1) * 10) + message[start + 3] + 1

                            profile_num = message[start + 5] + 1
                            return LampProfile(lamp_num=lamp_num, profile_num=profile_num)
                    case _:
                        return False
            case ParseCode.PCHAR:
                match message[start + 3]:
                    case ParseCode.NCHAR:
                        if length == 13:
                            profile_num = (message[start + 2] + 1)
                            name = message[start + 4:start + 12].decode('utf-8').rstrip('\x00')
                            return ProfileName(profile_num = profile_num, name=name)
                    case ParseCode.DCHAR:
                        if length == 6:
                            profile_num = message[start + 2] + 1
                            delay = message[start + 4]

                            return ProfileDelay(profile_num=profile_num, delay=delay)
                    case ParseCode.BCHAR:
                        if length == 8:
                            match message[start + 5]:
                                case ParseCode.VCHAR:
                                    profile_num = message[start + 2] + 1
                                    brighness_num = message[start + 4] + 1
                                    percent = message[start + 6]

                                    return ProfileBrightnessPercent(profile_num=profile_num, brightness_num=brighness_num, percent=percent)
                                case _:
                                    return False
            case _:
                return False


    def OpenPort(self, tty_port):
        if self.tty_serial.is_open:
            self.tty_serial.close()
        self.tty_serial.port = tty_port
        self.tty_serial.open()


    def SendVersionCmd(self):
        self.tty_serial.write(b'<V>')
        self.tty_serial.flush()
        response = self.tty_serial.read(5)
        
        if len(response) < 5 or response[0] != ParseCode.OPENBRACKET or response[4] != ParseCode.CLOSEBRACKET:
            print(f"ERROR: Unable to read firmware version from LED OCD: {response}")
            parsed = False
        elif response[1] == ParseCode.GCHAR:
            print("ERROR: This appears to be a GI OCD. Use different config software")
            parsed = False
        else:
            parsed = self.ParseMessage(response, 0, 5)
            
        return response, parsed


    def SendReadSettingsCmd(self):        
        self.tty_serial.write(b'<Q>')
        self.tty_serial.flush()
        response = self.tty_serial.read(2000)
        
        total_bytes = len(response)
        
        valid = True
        match total_bytes:
            case 1118:
                if self.manufacturer != Manufacturers.WPC:
                    valid = False
            case 1230:
                if self.manufacturer != Manufacturers.STERN:
                    valid = False
            case 1124 | 1127:
                if self.manufacturer != Manufacturers.CAPCOMA:
                    valid = False
            case 1130 | 1133:
                if self.manufacturer != Manufacturers.CAPCOMB:
                    valid = False
            case _:
                valid = False

        if valid:
            new_settings = []

            buffer = bytearray(response)
            total_bytes = len(buffer)
            
            found_sync = -1
            for x in range(0, total_bytes):
                if found_sync == -1:
                    if buffer[x] == ParseCode.OPENBRACKET:
                        found_sync = x
                elif buffer[x] == ParseCode.CLOSEBRACKET:
                    parsed = self.ParseMessage(buffer, found_sync, x-found_sync+1)
                    if parsed and parsed.__class__ in [ProfileName, ProfileBrightnessPercent, ProfileDelay, LampProfile]:
                        new_settings.append(parsed)
                    found_sync = -1

            # if (self.manufacturer in [Manufacturers.WPC, Manufacturers.CAPCOMA, Manufacturers.CAPCOMB] \
            #             and len(new_settings) == SETTINGS_OBJ_CNT_WPC) \
            #         or (self.manufacturer == Manufacturers.STERN and len(new_settings) == SETTINGS_OBJ_CNT_STERN):
            valid = self.ValidateSettings(new_settings)
            if valid:
                self.settings = new_settings
            # else:
            #     valid = False
                
        return response, self.settings if valid else response, False


    def SendSaveSettingsCmd(self):
        numbytes_sent = self.tty_serial.write(b'<S>')
        self.tty_serial.flush()
        if numbytes_sent != 3:
            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 3")
            return False
        else:
            return True


    def SendNormalOCDCmd(self):
        numbytes_sent = self.tty_serial.write(b'<T\x00>')
        self.tty_serial.flush()
        if numbytes_sent != 4:
            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 4")
            return False
        else:
            return True


    def SendManualCmd(self):
        numbytes_sent = self.tty_serial.write(b'<T\x01>')
        self.tty_serial.flush()

        if numbytes_sent != 4:
            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 4")
            return False

        # Turn off all lamps so you can focus on the one you want
        maxrow = 10 if self.manufacturer == Manufacturers.STERN else 8    
        for col in range(1, 9):
            for row in range(1, maxrow+1):
                cmd = bytearray(b'<L')
                cmd.append(col-1)
                cmd.append(row-1)
                cmd += b'B\x00>'
        
                self.tty_serial.write(cmd)
                self.tty_serial.flush()

        return True


    def SendPassthroughCmd(self):
        numbytes_sent = self.tty_serial.write(b'<T\x02>')
        self.tty_serial.flush()
        if numbytes_sent != 4:
            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 4")
            return False
        else:
            return True


    def ValidateSettings(self, settings):
        if not settings:
            print ("ERROR: There are no settings")
            return False

        match self.manufacturer:
            case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                lamp_profiles = [x for x in range(11, 89) if x%10 >= 1 and x%10 <= 8]
            case Manufacturers.STERN:
                lamp_profiles = [x for x in range(1, 81)]

        profile_names = list(range(1, 9))
        profile_delays = list(range(1, 9))
        profile_brights = {
            1: list(range(1, 9)),
            2: list(range(1, 9)),
            3: list(range(1, 9)),
            4: list(range(1, 9)),
            5: list(range(1, 9)),
            6: list(range(1, 9)),
            7: list(range(1, 9)),
            8: list(range(1, 9))
        }
        profile_brights_profiles = list(profile_brights.keys())

        for curr_setting in settings:
            cls = curr_setting.__class__
            if cls == LampProfile:
                if curr_setting.lamp_num in lamp_profiles:
                    if curr_setting.profile_num >= 1 and curr_setting.profile_num <= 8:
                        lamp_profiles.remove(curr_setting.lamp_num)
                    else:
                        print (f"ERROR: LampProfile - invalid profile number ({curr_setting.profile_num}) - should be >= 1 and <= 8")
                        return False
                else:
                    print (f"ERROR: LampProfile - invalid or duplicate lamp number ({curr_setting.lamp_num})")
                    return False

            elif cls == ProfileName:
                if curr_setting.profile_num in profile_names:
                    if len(curr_setting.name) >= 0 and len(curr_setting.name) <= 8:
                        profile_names.remove(curr_setting.profile_num)
                    else:
                        print (f"ERROR: ProfileName - invalid name \"{curr_setting.name}\" length ({len(curr_setting.name)}) - should be 1 to 8 characters")
                        return False
                else:
                    print (f"ERROR: ProfileName - invalid or duplicate profile number ({curr_setting.profile_num})")
                    return False

            elif cls == ProfileDelay:
                if curr_setting.profile_num in profile_delays:
                    if curr_setting.delay >= 0 and curr_setting.delay <= 9:
                        profile_delays.remove(curr_setting.profile_num)
                    else:
                        print (f"ERROR: ProfileDelay - invalid delay \"{curr_setting.delay}\" - should be >= 0 and <= 9")
                        return False
                else:
                    print (f"ERROR: ProfileDelay - invalid or duplicate profile number ({curr_setting.profile_num})")
                    return False

            elif cls == ProfileBrightnessPercent:
                if curr_setting.profile_num in profile_brights_profiles:
                    if curr_setting.brightness_num in profile_brights[curr_setting.profile_num]:
                        if curr_setting.percent >= 0 and curr_setting.percent <= 100:
                            profile_brights[curr_setting.profile_num].remove(curr_setting.brightness_num)
                            if len(profile_brights[curr_setting.profile_num]) == 0:
                                profile_brights_profiles.remove(curr_setting.profile_num)
                                del profile_brights[curr_setting.profile_num]
                        else:
                            print (f"ERROR: ProfileBrightnessPercent - invalid brigthness percent ({curr_setting.percent}) for profile #{curr_setting.profile_num}) brightness #{curr_setting.brightness_num} - must be 0 to 100")
                            return False
                    else:
                        print (f"ERROR: ProfileBrightnessPercent - invalid or duplicate profile brightness ({curr_setting.brightness_num}) for profile #{curr_setting.profile_num})")
                        return False
                else:
                    print (f"ERROR: ProfileBrightnessPercent - invalid or duplicate profile number ({curr_setting.profile_num})")
                    return False
                
        if not len(lamp_profiles) == 0:
            print(f"ERROR: One or more missing LampProfile settings")
            return False
        if not len(profile_names) == 0:
            print(f"ERROR: One or more missing ProfileName settings")
            return False
        if not len(profile_delays) == 0:
            print(f"ERROR: One or more missing ProfileDelay settings")
            return False
        if not len(profile_brights) == 0:
            print(f"ERROR: One or more missing ProfileBrightnessPercent settings")
            return False

        return True


    def UpdateSettings(self, manufacturer, new_settings):
        if not (manufacturer >= 0 and manufacturer <= 3):
            return FALSE
        
        self.manufacturer = manufacturer

        if self.ValidateSettings(new_settings):
            self.settings = []
            for obj in new_settings:
                self.settings.append(obj)
            return True
        else:
            return False


    def SendSettings(self):
        if self.settings and self.ValidateSettings(self.settings):
            result = True
            for curr_setting in self.settings:
                if hasattr(curr_setting, 'SendTo'):
                    result = curr_setting.SendTo(led_ocd=self)
                else:
                    return False

                if not result:
                    return False
        else:
            return False

        return True


    def SendSetPNCmd(self, pnum, pname):
        if pnum >= 1 and pnum <= 8:
            if len(pname) >= 1 and len(pname) <= 8:
                cmd = bytearray(b'<P')
                cmd.append(pnum-1)
                cmd += b'N'
                cmd += bytes(pname.ljust(8, '\0'), 'utf-8')
                cmd += b'>'
                
                numbytes_sent = self.tty_serial.write(cmd)
                self.tty_serial.flush()
                if numbytes_sent == 13:
                    return True
                else:
                    print(f"Error: Number of bytes sent ({numbytes_sent}) was not 13")
                    return False
            else:
                print(f"Invalid SetPN command: profile name \"{pname}\" must be 1-8 characters long")
                return False
        else:
            print(f"Invalid SetPN command: profile number {pnum} must be (1-8)")
            return False


    def SendSetPBCmd(self, pnum, brightnum, value):
        if pnum >= 1 and pnum <= 8:
            if brightnum >= 1 and brightnum <= 8:
                if value >= 0 and value <= 100:
                    if value == 62:
                        # 62 is the same as '>', so it causes parsing errors on the LED OCD firmware
                        value = 63
                    
                    cmd = bytearray(b'<P')
                    cmd.append(pnum-1)
                    cmd += b'B'
                    cmd.append(brightnum)
                    cmd += b'V'
                    cmd.append(value)
                    cmd += b'>'
                    
                    numbytes_sent = self.tty_serial.write(cmd)
                    self.tty_serial.flush()
                    if numbytes_sent == 8:
                        return True
                    else:
                        print(f"Error: Number of bytes sent ({numbytes_sent}) was not 8")
                        return False
                else:
                    print(f"Invalid SetPB command: profile number ({pnum}) must be 1-8")
                    return False
            else:
                print(f"Invalid SetPB command: brightness number ({brightnum}) must be 1-8")
                return False
        else:
            print(f"Invalid SetPB command: brightness value ({value}) must be 0-100")
            return False


    def SendSetPDCmd(self, pnum, delay):
        if pnum >= 1 and pnum <= 8:
            if delay >= 0 and delay <= 9:
                cmd = bytearray(b'<P')
                cmd.append(pnum-1)
                cmd += b'D'
                cmd.append(delay)
                cmd += b'>'
                
                numbytes_sent = self.tty_serial.write(cmd)
                self.tty_serial.flush()
                if numbytes_sent == 6:
                    return True
                else:
                    print(f"Error: Number of bytes sent ({numbytes_sent}) was not 6")
                    return False
            else:
                print(f"Invalid SetPD command: delay ({delay}) must be 0-9")
                return False
        else:
            print(f"Invalid SetPD command: profile number ({pnum}) must be 1-8")
            return False


    def SendSetLPCmd(self, lampnum, pnum):
        if pnum >= 1 and pnum <= 8:
            if lampnum >= 1 and lampnum <= 88:
                maxrow = 10 if self.manufacturer == Manufacturers.STERN else 8
                
                if self.manufacturer == Manufacturers.STERN:
                    col = ((lampnum - 1) % 8) + 1
                    row = ((lampnum - 1) // 8) + 1
                else:
                    col = lampnum // 10
                    row = lampnum % 10

                if row >= 1 and row <= maxrow:
                    if col >= 1 and col <= 8:
                        cmd = bytearray(b'<L')
                        cmd.append(col-1)
                        cmd.append(row-1)
                        cmd += b'P'
                        cmd.append(pnum-1)
                        cmd += b'>'
                
                        numbytes_sent = self.tty_serial.write(cmd)
                        self.tty_serial.flush()
                        if numbytes_sent == 7:
                            return True
                        else:
                            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 7")
                            return False
            else:
                print(f"Invalid SETLP command: lamp num ({lampnum}) must be 1-88")
                return False
        else:
            print(f"Invalid SETLP command: profile number ({pnum}) must be 1-8")
            return False


    def SendSetLBCmd(self, lampnum, bright):
        if bright >= 1 and bright <= 8:
            if lampnum >= 1 and lampnum <= 88:
                maxrow = 10 if self.manufacturer == Manufacturers.STERN else 8
                
                if self.manufacturer == Manufacturers.STERN:
                    col = ((lampnum - 1) % 8) + 1
                    row = ((lampnum - 1) // 8) + 1
                else:
                    col = lampnum // 10
                    row = lampnum % 10

                if row >= 1 and row <= maxrow:
                    if col >= 1 and col <= 8:
                        cmd = bytearray(b'<L')
                        cmd.append(col-1)
                        cmd.append(row-1)
                        cmd += b'B'
                        cmd.append(bright)
                        cmd += b'>'
                
                        numbytes_sent = self.tty_serial.write(cmd)
                        self.tty_serial.flush()
                        if numbytes_sent == 7:
                            return True
                        else:
                            print(f"Error: Number of bytes sent ({numbytes_sent}) was not 7")
                            return False
            else:
                print(f"Invalid SetLB command: lamp num ({lampnum}) must be 1-88")
                return False
        else:
            print(f"Invalid SetLB command: brightness number ({bright}) must be 0-8")
            return False


    def SendCheckCmd(self):
        # Switch to manual mode
        if not self.SendManualCmd():
            print ("Error: Couldn't switch to manual mode for Check command")
            return False
        
        # Draw the checkboard
        maxrow = 10 if self.manufacturer == Manufacturers.STERN else 8    
        for col in range(1, 9):
            for row in range(1, maxrow+1):
                cmd = bytearray(b'<L')
                cmd.append(col-1)
                cmd.append(row-1)
                cmd += b'B'
                cmd.append(((col + row) % 2) * 8)
                cmd += b'>'
        
                self.tty_serial.write(cmd)
                self.tty_serial.flush()

        return True
