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


class Watchdog:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(value={self.value})'
        return s


class LampProfile:
    def __init__(self, lamp_num, profile_num):
        self.lamp_num = lamp_num
        self.profile_num = profile_num

    def __repr__(self):
        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(lamp_num={self.lamp_num}, profile_num={self.profile_num})'
        return s

    def to_dict(self):
        return {
            "class": "LampProfile",
            "lamp_num": self.lamp_num,
            "profile_num": self.profile_num
        }

    def SendTo(self, led_ocd):
        return led_ocd.SendSetLPCmd(lampnum=self.lamp_num, pnum=self.profile_num)


class ProfileName:
    def __init__(self, profile_num, name):
        self.profile_num = profile_num
        self.name = name

    def __repr__(self):
        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(profile_num={self.profile_num}, name="{self.name}")'
        return s

    def to_dict(self):
        return {
            "class": "ProfileName",
            "profile_num": self.profile_num,
            "name": self.name
        }

    def SendTo(self, led_ocd):
        return led_ocd.SendSetPNCmd(pnum=self.profile_num, pname=self.name)
    

class ProfileDelay:
    def __init__(self, profile_num, delay):
        self.profile_num = profile_num
        self.delay = delay

    def __repr__(self):
        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(profile_num={self.profile_num}, delay={self.delay})'
        return s

    def to_dict(self):
        return {
            "class": "ProfileDelay",
            "profile_num": self.profile_num,
            "delay": self.delay
        }

    def SendTo(self, led_ocd):
        return led_ocd.SendSetPDCmd(pnum=self.profile_num, delay=self.delay)


class ProfileBrightnessPercent:
    def __init__(self, profile_num, brightness_num, percent):
        self.profile_num = profile_num
        self.brightness_num = brightness_num
        self.percent = percent

    def __repr__(self):
        s = f'{self.__class__.__module__}.{self.__class__.__qualname__}(profile_num={self.profile_num}, brightness_num={self.brightness_num}, percent={self.percent})'
        return s

    def to_dict(self):
        return {
            "class": "ProfilesBrightnessPercent",
            "profile_num": self.profile_num,
            "brightness_num": self.brightness_num,
            "percent": self.percent
       }

    def SendTo(self, led_ocd):
        return led_ocd.SendSetPBCmd(pnum=self.profile_num, brightnum=self.brightness_num, value=self.percent)
