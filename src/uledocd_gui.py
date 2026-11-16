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

from serial.tools import list_ports
import serial
from ttkbootstrap import *
from ttkbootstrap.widgets import ToolTip
from tkinter.constants import BOTH, YES, NO
from platformdirs import PlatformDirs
import shutil

import platform
import argparse
import csv
import os
import re
import datetime
import xml.etree.ElementTree as ET
import glob

from uledocd import ULEDOCD, Manufacturers
from packets import LampProfile, ProfileName, ProfileBrightnessPercent, ProfileDelay

MIN_WIDTH               = 1010
MIN_HEIGHT              = 600

DEFAULT_STERN_GAME      = "-Undefined Stern"
DEFAULT_WPC_GAME        = "-Undefined WPC-Sys11-DE"

DEFAULT_DATA_DIR        = "data"
GAMES_SUBDIR            = "games"
SETTINGS_SUBDIR         = "settings"
BACKUPS_SUBDIR          = "backups"
OPTIONS_SUBDIR          = "options"

OPTIONS_FILE                = "options.xml"
DATA_FILE                   = "data.xml"
DEFAULT_WPC_SETTINGS_XML    = "default_wpc_settings.xml"
DEFAULT_STERN_SETTINGS_XML  = "default_stern_settings.xml"

SETTINGS_OBJ_CNT        = 168
SETTINGS_OBJ_CNT_WPC    = 144
SETTINGS_OBJ_CNT_STERN  = 160

Manu_String_to_ID = {
    "WPC": Manufacturers.WPC,
    "CAPCOM_A": Manufacturers.CAPCOMA,
    "CAPCOM_B": Manufacturers.CAPCOMB,
    "STERN": Manufacturers.STERN
}

Manu_ID_to_String = {
    Manufacturers.WPC: "WPC",
    Manufacturers.CAPCOMA: "CAPCOM_A",
    Manufacturers.CAPCOMB: "CAPCOM_B",
    Manufacturers.STERN: "STERN"
}

Manu_ID_to_Default_XML = {
    Manufacturers.WPC: DEFAULT_WPC_SETTINGS_XML,
    Manufacturers.CAPCOMA: DEFAULT_WPC_SETTINGS_XML,
    Manufacturers.CAPCOMB: DEFAULT_WPC_SETTINGS_XML,
    Manufacturers.STERN: DEFAULT_STERN_SETTINGS_XML
}

# Function to validate input length
def limit_input_length(input_text, length_limit):
    if len(input_text) > int(length_limit):
        return False
    return True


# Function to validate input value
def limit_num(input_text, min, max):
    if input_text == "":
        return True

    try:
        i = int(input_text)
    except:
        return False
    
    if i < int(min) or i > int(max):
        return False
    return True


# Function to distribute numbers between a start and stop value in a specified number of values
def gen_nums(start, stop, nums):
    cnt = nums-1
    vals = [int(start + x*(stop-start)/cnt) for x in range(cnt)]
    vals.append(stop)
    return vals


class ULEDOCD_GUI:
    def __init__(self, port_name=None, manufacturer=Manufacturers.WPC, data_dir=None, game_file=None):
        self.led_ocd = None

        self.gui_when_disconnected = []
        self.gui_when_connected = []

        self.gui_in_advanced = []
        self.gui_in_manual_advanced = []
        
        self.gui_in_normal = []
        self.gui_in_manual = []

        self.lamp_menus_list = []
        self.lamp_menu_buttons_dict = {}
        self.lamp_vars_dict = {}
        self.lamp_num_labels_dict = {}
        self.lamp_name_labels_dict ={}
        self.lamp_profile_name_labels_dict = {}
        self.grid_items = []
        self.game_menu = None
        self.game_menu_button = None
        self.port_menu_button = None
        self.port_menu = None
        self.settings = {}
        self.port_name = port_name
        self.data_dir = None
        self.game_file = None
        self.manual_mode = False
        self.name_dict = {}
        self.progress_window = None
        self.passthru_window = None
        self.options_window = None
        self.options = {}
        self.data = {}
        self.reverse_sort = False
        self.last_sort = 0

        self.dirs = PlatformDirs("uledocd", "novibing", ensure_exists=True)
        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = self.dirs.user_data_dir

        self.backups_dir = os.path.join(self.data_dir, BACKUPS_SUBDIR)
        default_backups_dir = os.path.join(self.script_dir, DEFAULT_DATA_DIR, BACKUPS_SUBDIR)

        self.games_dir = os.path.join(self.data_dir, GAMES_SUBDIR)
        default_games_dir = os.path.join(self.script_dir, DEFAULT_DATA_DIR, GAMES_SUBDIR)

        self.settings_dir = os.path.join(self.data_dir, SETTINGS_SUBDIR)
        default_settings_dir = os.path.join(self.script_dir, DEFAULT_DATA_DIR, SETTINGS_SUBDIR)

        self.options_dir = self.dirs.user_preference_dir
        self.options_file = os.path.join(self.options_dir, OPTIONS_FILE)
        default_options_file = os.path.join(self.script_dir, DEFAULT_DATA_DIR, OPTIONS_SUBDIR, OPTIONS_FILE)

        if not os.path.exists(self.data_dir):
            print (f"The data directory (\"{self.data_dir}\") doesn't exist. Make sure the data directory and its subdirectories (games, backups and settings) exist and are populated and try again.")
            return
        if not os.path.exists(self.games_dir):
            shutil.copytree(default_games_dir, self.games_dir, dirs_exist_ok=True)
        if not os.path.exists(self.settings_dir):
            shutil.copytree(default_settings_dir, self.settings_dir, dirs_exist_ok=True)
        if not os.path.exists(self.backups_dir):
            shutil.copytree(default_backups_dir, self.backups_dir, dirs_exist_ok=True)                              
        if not os.path.exists(self.options_file):
            os.makedirs(self.options_dir, exist_ok=True)
            shutil.copy2(default_options_file, self.options_file)

        self.app=App()
        self.app.resizable(True, True)
        self.app.withdraw()
        self.app.update_idletasks()

        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        # On macOS we also need to intercept File->Quit and Command-Q.
        if platform.system().lower() == "darwin":
            self.app.createcommand("::tk::mac::Quit", self.on_closing)

        self.style = self.app.style
        self.style.configure("gray.TFrame", background="gray30")

        # Register validation function
        self.val_text = self.app.register(limit_input_length)
        self.val_num = self.app.register(limit_num)

        # App variables
        self.selected_port = StringVar()
        self.selected_game_name = StringVar()
        self.selected_sort = IntVar()
        self.manu_id = IntVar()
        self.manufacturer = StringVar()
        self.result = StringVar()
        self.selected_manual_lamp = IntVar(self.app)
        self.selected_brightnesss_num = IntVar(self.app)
        self.selected_keep_profile_num = IntVar(self.app)

        lamp_vars = []
        for lnum in range(1, 89):
            var_name = "Lamp{:02d}".format(lnum)
            lamp_vars.append(IntVar(self.app, name=var_name))

        self.settings.update({"lamp_vars": lamp_vars})

        self.app.title("Unofficial LED OCD")
        self.app.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Frame for the whole window
        self.app_frame = Frame(self.app)
        self.app_frame.pack(fill=BOTH, expand=YES)
        self.app_frame.pack_propagate(0)


        # Frames to split the window into two overall areas with bordering frames that expand
        self.app_frame_left_border = Frame(self.app_frame, padding=1, style='gray.TFrame')
        self.app_frame_left_border.pack(side='left', fill='both', expand=True)
        # self.app_frame_left_border.pack_propagate(0)

        self.app_frame_left = Frame(self.app_frame, padding=1, bootstyle="@card")
        self.app_frame_left.pack(side='left', fill='y', expand=False)
        # self.app_frame_left.pack_propagate(0)

        self.app_frame_right = Frame(self.app_frame, padding=1, bootstyle="@card")
        self.app_frame_right.pack(side='left', fill='y', expand=False)
        # self.app_frame_right.pack_propagate(0)

        self.app_frame_right_border = Frame(self.app_frame, padding=1, style='gray.TFrame')
        self.app_frame_right_border.pack(side='left', fill='both', expand=True)
        # self.app_frame_right_border.pack_propagate(0)


        # Frames on the left side
        self.app_frame_left_0 = Frame(self.app_frame_left, bootstyle="@card")
        self.app_frame_left_0.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)

        self.app_frame_left_1 = ScrolledFrame(self.app_frame_left, bootstyle="@card")
        self.app_frame_left_1.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        # Frames on the right side
        self.app_frame_right_0 = Frame(self.app_frame_right)
        self.app_frame_right_0.grid(sticky="ew", column=0, row=0, padx=3, pady=3)

        self.app_frame_right_1 = Frame(self.app_frame_right)
        self.app_frame_right_1.grid(sticky="ew", column=0, row=2, padx=3, pady=3)

        self.app_frame_right_2 = Frame(self.app_frame_right)
        self.app_frame_right_2.grid(sticky="ew", column=0, row=1, padx=3, pady=3)

        self.app_frame_right_3 = Frame(self.app_frame_right)
        self.app_frame_right_3.grid(sticky="ew", column=0, row=3, padx=3, pady=3)

        self.app_frame_right_4 = Frame(self.app_frame_right)
        self.app_frame_right_4.grid(sticky="nsew", column=0, row=4, padx=3, pady=3)

        self.app_frame_right_5 = Frame(self.app_frame_right)
        self.app_frame_right_5.grid(sticky="nsew", column=0, row=5, padx=3, pady=3)


        # self.app_frame_left.columnconfigure(0, weight=1)
        self.app_frame_left.rowconfigure(1, weight=1)

        # self.app_frame_right.columnconfigure(0, weight=1)
        self.app_frame_right.rowconfigure(4, weight=1)

        if manufacturer:
            manu_id = Manu_String_to_ID[manufacturer.upper()]
            if manu_id:
                self.manu_id.set(manu_id)
            else:
                self.manu_id.set(Manufacturers.WPC)
        else:
            self.manu_id.set(Manufacturers.WPC)

        self.read_button = Button(self.app_frame_right_2, text="Read", command=self.ReadButtonClicked)
        ToolTip(self.read_button, text="Read the current settings from the LED OCD board and update the GUI with those settings")
        self.read_button.grid(sticky="nw", column=0, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.read_button)
        self.gui_in_normal.append(self.read_button)

        self.send_button = Button(self.app_frame_right_2, text="Send", command=self.SendButtonClicked)
        ToolTip(self.send_button, text="Send the current settings to the LED OCD board - they take effect, but are cleared after a power cycle")
        self.send_button.grid(sticky="nw", column=1, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.send_button)
        self.gui_in_normal.append(self.send_button)

        self.save_button = Button(self.app_frame_right_2, text="Save", command=self.SaveButtonClicked)
        ToolTip(self.save_button, text="Save the current settings to the LED OCD board - they will be in effect after a power cycle")
        self.save_button.grid(sticky="nw", column=2, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.save_button)
        self.gui_in_normal.append(self.save_button)

        self.import_button = Button(self.app_frame_right_2, text="Import", command=self.ImportButtonClicked)
        ToolTip(self.import_button, text="Import settings from a file")
        self.import_button.grid(sticky="ne", column=3, row=0, padx=(187,5), pady=5)
        self.gui_in_normal.append(self.import_button)

        self.export_button = Button(self.app_frame_right_2, text="Export", command=self.ExportButtonClicked)
        ToolTip(self.export_button, text="Export settings to a file")
        self.export_button.grid(sticky="ne", column=4, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.export_button)
        self.gui_in_normal.append(self.export_button)

        self.manual_button = Button(self.app_frame_right_3, text="Manual Mode", command=self.ManualButtonClicked)
        ToolTip(self.manual_button, text="Manual Mode allows you to test individual lamps to find what brightness values look best")

        self.manual_button.grid(sticky="nw", column=0, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.manual_button)
        self.gui_in_normal.append(self.manual_button)

        self.passthrough_button = Button(self.app_frame_right_3, text="Passthrough", command=self.PassthroughButtonClicked)
        ToolTip(self.passthrough_button, text="Passthrought allows you to temporarily disable LED OCD to simulate 'raw' LEDs")
        self.passthrough_button.grid(sticky="nw", column=1, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.passthrough_button)
        self.gui_in_normal.append(self.passthrough_button)

        self.app_frame_right_3.update()

        self.log = ScrolledText(self.app_frame_right_4, auto_hide=True, padding=3, width=61, font=("Arial", 10))
        # self.log = ScrolledText(self.app_frame_right_4, auto_hide=True, font=("Arial", 10))
        self.log.text.configure(state="disabled", font=("Arial", 10), wrap="word")
        self.log.text.tag_configure("time", background="white", foreground="gray60")
        self.log.text.tag_configure("info", background="white", foreground="black")
        self.log.text.tag_configure("warning", background="yellow", foreground="black")
        self.log.text.tag_configure("error", background="#AA0000", foreground="white")
        self.log.pack(fill="both", expand=True, padx=3, pady=3)
        self.result.trace_add('write', self.update_log)

        self.settings_button = Button(self.app_frame_right_5, icon="gear", command=self.show_options)
        self.settings_button.pack(side='right', padx=3, pady=3)

        self.app_frame_right_4.update()
        self.app_frame_right_4.configure()


        self.load_data()
        self.app.geometry(self.data["geometry"])

        self.load_options()

        self.build_port_menu()        
        self.build_game_menu()
        self.build_lamp_matrix()    # This must come before build_lamp_menu() because build_lamp_menu()
                                    # needs the profile names to already be created and those are created
                                    # in build_lamp_matrix()
        self.build_lamp_menu()
        self.build_manual_widgets()

        if not game_file:
            if self.options["on_startup"]["select_last_game"].get() and self.data["last_game"] != "":
                game_file = self.data["last_game"] + ".csv"

        # Set selected or default game
        file_found = False
        if game_file:
            gfile = os.path.basename(game_file)
            pattern = r".*\.csv$"
            
            for f in os.listdir(self.games_dir):
                if (not file_found) and re.search(pattern, f):
                    if f == gfile:
                        file_found = True
                        game = os.path.splitext(gfile)[0]
            if not file_found:
                self.result.set(f"WARNING: The game file \"{gfile}\" does not exist in the games directory (\"{self.games_dir}\"), using default game")

        if not file_found:
            match self.manu_id.get():
                case Manufacturers.STERN:
                    game = DEFAULT_STERN_GAME
                case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                    game = DEFAULT_WPC_GAME
                case _:
                    self.manu_id.set(Manufacturers.WPC)
                    game = DEFAULT_WPC_GAME

        self.app.after(250, self.after_startup, game)

        for x in self.gui_when_disconnected:
            x.state(["!disabled"])

        for x in self.gui_when_connected:
            x.state(["disabled"])

        for x in self.gui_in_manual:
            x.state(["disabled"])

        self.led_ocd = ULEDOCD(self.manu_id.get())

        if not self.options["on_startup"]["import_last_backup"].get():
            if self.manu_id.get() == Manufacturers.STERN:
                default_settings_xml = DEFAULT_STERN_SETTINGS_XML
            else:
                default_settings_xml = DEFAULT_WPC_SETTINGS_XML
            settings_file = os.path.join(self.settings_dir, default_settings_xml)
            if os.path.exists(settings_file):
                self.load_from_xml_file(settings_file)
            else:
                self.result.set(f"WARNING: The default settings file (\"{settings_file}\") doesn't exist. Can't load default settings.")

        if self.advanced.get():
            for x in self.gui_in_advanced:
                x.configure(state="!disabled", takefocus=True)
            for x in self.gui_in_manual_advanced:
                x.configure(state="!disabled", takefocus=True)
        else:
            for x in self.gui_in_advanced:
                x.configure(state="disabled", takefocus=False)
            for x in self.gui_in_manual_advanced:
                x.configure(state="disabled", takefocus=False)

        self.app.update()
        self.app.mainloop()


    # def resize(self, event):
    #     if event.widget == self.app:
    #         if self.grid_items:
                # self.draw_lamp_rows()

            # self.app_frame_left_1.update()
            # self.app.update()
            # self.app.geometry(f"{event.height}x{event.width}")


    def on_closing(self):
        # If the progress window is up don't quit unless we are stuck. close_if_no_progress
        # checks to see if progress is stuck. If it remains stuck for at least 6 seconds it
        # will close the app. If progress is completed during those checks it will not quit
        # and the user can quit in a normal, clean fashion.
        if self.progress_window:
            self.stuck_count = 0
            self.last_progress = self.progress
            self.app.after(2000, self.close_if_no_progress)
            return

        if self.options_window:
            return
        
        # If in manual mode or passthrough mode switch back to NormalOCD mode before qutting
        if self.manual_mode:
            self.led_ocd.SendNormalOCDCmd()

        self.save_data()
        self.save_options()
        self.app.destroy()


    def close_if_no_progress(self):
        # If we haven't made progress for 6+ seconds than close the progress window and quit the app
        if self.progress_window:
            if self.progress == self.last_progress:
                self.stuck_count += 1
                if self.stuck_count >= 3:
                    self.close_progress()
                    self.on_closing()
                else:
                    self.app.after(2000, self.close_if_no_progress)

            else:
                self.stuck_count = 0
                self.last_progress = self.progress
                self.app.after(2000, self.close_if_no_progress)


    def after_startup(self, game):
        if game:
            self.selected_game_name.set(game)
            
        if self.options["on_startup"]["import_last_backup"].get():
            pattern = os.path.join(self.backups_dir, "*.xml")
            try:
                last_backup_file = max(glob.iglob(pattern),key=os.path.getctime)
            except:
                last_backup_file = None

            if last_backup_file:
                if self.load_from_xml_file(last_backup_file):
                    self.result.set(f"Successfully imported latest backup (\"{last_backup_file}\")")
                else:
                    self.result.set(f"ERROR: Could not import the latest backup (\"{last_backup_file}\") file")

        self.build_port_list()
        self.result.set("Ready. Select the Serial Port and Connect to begin.")
        self.app.deiconify()


    def load_options(self):
        try:
            tree = ET.parse(self.options_file)
        except FileNotFoundError:
            # If the options file doesn't exist use default options
            self.options = {
                "on_startup": {
                    "select_last_game": BooleanVar(value=True),
                    "import_last_backup": BooleanVar(value=False),
                    "select_last_port": BooleanVar(value=True),
                },
                "backups": {
                    "on_read": BooleanVar(value=True),
                    "on_send": BooleanVar(value=True),
                    "limit_to": IntVar(value=20),
                },
                "other": {
                    "verify_sends": BooleanVar(value=True),
                }
            }
            return
        
        root = tree.getroot()

        limit_to = root.findtext("backups/limit_to")

        self.options = {
            "on_startup": {
                "select_last_game": BooleanVar(value=root.findtext("on_startup/select_last_game").lower() == "true"),
                "import_last_backup": BooleanVar(value=root.findtext("on_startup/import_last_backup").lower() == "true"),
                "select_last_port": BooleanVar(value=root.findtext("on_startup/select_last_port").lower() == "true"),
            },
            "backups": {
                "on_read": BooleanVar(value=root.findtext("backups/on_read").lower() == "true"),
                "on_send": BooleanVar(value=root.findtext("backups/on_send").lower() == "true"),
                "limit_to": IntVar(value=int(limit_to) if limit_to != "" else 0),
            },
            "other": {
                "verify_sends": BooleanVar(value=root.findtext("other/verify_sends").lower() == "true"),
            }
        }


    def save_options(self):
        declaration = '<?xml version="1.0" encoding="utf-8"?>\n'

        root = ET.Element("options")
        category_keys = self.options.keys()
        for curr_cat_key in category_keys:
            curr_category = ET.SubElement(root, curr_cat_key)
            curr_option_keys = self.options[curr_cat_key].keys()
            for curr_option_key in curr_option_keys:
                curr_option = ET.SubElement(curr_category, curr_option_key)
                curr_type = self.options[curr_cat_key][curr_option_key].__class__
                if curr_type == BooleanVar:
                    curr_option.text = "true" if self.options[curr_cat_key][curr_option_key].get() else "false"
                elif curr_type == IntVar:
                    curr_option.text = "{:d}".format(self.options[curr_cat_key][curr_option_key].get())
                elif curr_type == StringVar:
                    curr_option.text = self.options[curr_cat_key][curr_option_key].get()

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)

        with open (self.options_file, "wb") as f:
            f.write(declaration.encode("utf-8"))
            tree.write(f, encoding="utf-8")

        return True


    def load_data(self):
        self.data = {}
        data_file_path = os.path.join(self.settings_dir, DATA_FILE)
        try:
            tree = ET.parse(data_file_path)
        except FileNotFoundError:
            # If the data file doesn't exist use default data
            self.data["last_game"] = ""
            self.data["last_port"] = ""
            self.data["geometry"] = str(MIN_WIDTH) + "x" + str(MIN_HEIGHT)
            return
        
        root = tree.getroot()

        self.data["last_game"] = root.findtext("last_game")
        self.data["last_port"] = root.findtext("last_port")
        self.data["geometry"] = root.findtext("geometry")
        if self.data["geometry"] == "":
            self.data["geometry"] = str(MIN_WIDTH) + "x" + str(MIN_HEIGHT)


    def save_data(self):
        declaration = '<?xml version="1.0" encoding="utf-8"?>\n'

        root = ET.Element("data")

        last_game_e = ET.Element("last_game")
        last_game_e.text = self.selected_game_name.get()
        root.append(last_game_e)

        last_port_e = ET.Element("last_port")
        last_port_e.text = self.data["last_port"]
        root.append(last_port_e)

        geometry_e = ET.Element("geometry")
        geometry_e.text = str(self.app.winfo_width()) + "x" + str(self.app.winfo_height())
        root.append(geometry_e)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)

        data_file_path = os.path.join(self.settings_dir, DATA_FILE)
        with open (data_file_path, "wb") as f:
            f.write(declaration.encode("utf-8"))
            tree.write(f, encoding="utf-8")


    def open_progress(self, title=""):
        if not self.progress_window:
            x = self.app.winfo_x() + self.app.winfo_width()//2 - 300//2
            y = self.app.winfo_y() + self.app.winfo_height()//2 - 55//2
            self.progress_window = Toplevel(master=self.app, transient=self.app, window_type="splash", title=title, size=(300, 55), position=[x, y])
            self.progress_window.grab_set() 

            self.progress = IntVar(value=0)
            self.progress_gauge = Floodgauge(self.progress_window, variable=self.progress, maximum=100, mask="{}% complete",
                    bootstyle="info")

            self.progress_gauge.pack(padx=3, pady=3)
            self.progress_window.update()


    def set_progress_title(self, title):
        if self.progress_window:
            self.progress_window.title(title)
            self.progress_window.update()


    def set_progress(self, value):
        if self.progress_window:
            if value >= 0 and value <= 100:
                self.progress.set(value)
                self.progress_window.update()


    def close_progress(self):
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None


    def update_log(self, var_name, index, mode):
        result = self.result.get()
        timestr = '{date:%H:%M:%S}: '.format(date=datetime.datetime.now())
        log_str = timestr + result

        if result[:6].lower() == "error:":
            tag = "error"
        elif result[:8].lower() == "warning:":
            tag = "warning"
        else:
            tag = "info"

        self.log.text.configure(state="normal")
        if self.log.text.compare("end-1c", "==", "1.0"):
            self.log.text.insert("end", log_str)
        else:
            self.log.text.insert("end", "\n" + log_str)
        self.log.text.tag_add("time", 'end-1c linestart', 'end-1c linestart+10c')
        self.log.text.tag_add(tag, 'end-1c linestart+10c', 'end-1c')
        self.log.text.see("end")
        self.log.text.configure(state="disabled")


    def build_port_list(self):
        port_choices = list_ports.comports()
        self.port_list = []

        self.port_menu.delete(0, "end")

        for x in port_choices:
            self.port_list.append(x[0])

        if self.port_name:
            self. port_list.append(self.port_name)

        if len(self.port_list) >= 1:
            for port in self.port_list:
                self.port_menu.add_radiobutton(
                    label=port,
                    value=port,
                    variable=self.selected_port
                )

            # If the select_last_port option is set true, set the port to the last
            # successful port (the last port successfully connected to) if there
            # is one.
            if self.options["on_startup"]["select_last_port"].get() and self.data["last_port"] != "":
                if self.data["last_port"] in self.port_list:
                    self.selected_port.set(self.data["last_port"])

            # If the board is connected usually the correct port is the last one.
            # Select it if another port has not already been selected.
            if not self.selected_port.get():
                self.selected_port.set(self.port_list[-1])

        self.port_menu.configure()


    def build_port_menu(self):
        self.port_menu_button = Menubutton(self.app_frame_right_0, text="{:<32s}".format("Select USB serial port"), width=25)

        self.selected_port.trace_add('write', 
            lambda *args: self.port_menu_button.config(text="{:<32s}".format(self.selected_port.get()))
        )

        self.port_menu = Menu(self.app_frame_right_0, postcommand=self.build_port_list, tearoff=0)

        self.port_menu_button["menu"] = self.port_menu

        self.lbl = Label(self.app_frame_right_0, text = "Port:")
        self.lbl.grid(sticky="nsw", column=0, row=0, padx=3, pady=3)

        self.port_menu_button.grid(sticky="nw", column=1, row=0, padx=3, pady=3)
        self.gui_when_disconnected.append(self.port_menu_button)

        self.connect_button = Button(self.app_frame_right_0, text="Connect", command=self.ConnectButtonClicked)
        self.connect_button.grid(sticky="nw", column=2, row=0, padx=(30,3), pady=3)
        self.gui_when_disconnected.append(self.connect_button)

        self.disconnect_button = Button(self.app_frame_right_0, text="Disconnect", command=self.DisconnectButtonClicked)
        self.disconnect_button.grid(sticky="nw", column=3, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.disconnect_button)


    def build_game_menu(self):
        # Build the game selection menu
        self.game_files = []
        pattern = r".*\.csv$"
        for f in os.listdir(self.games_dir):
            if re.search(pattern, f):
                self.game_files.append(f)

        self.game_files = sorted(self.game_files)

        self.game_menu_button = Menubutton(self.app_frame_left_0, width=25, text='Select Game')
        self.game_menu = Menu(self.game_menu_button, tearoff=0)
        for file_name in self.game_files:
            game_name = os.path.splitext(file_name)[0]
            self.game_menu.add_radiobutton(
                label=game_name,
                value=game_name,
                variable=self.selected_game_name
            )
        self.game_menu.configure()
        self.game_menu_button["menu"] = self.game_menu
        self.game_menu_button.grid(sticky="nw", column=0, row=3, padx=3, pady=3)

        self.selected_game_name.trace_add('write', self.selected_game_callback)

        for file_name in self.game_files:
            game_name = os.path.splitext(file_name)[0]
            self.game_menu.add_radiobutton(
                label=game_name,
                value=game_name,
                variable=self.selected_game_name
            )
        self.game_menu.configure()
        self.game_menu_button["menu"] = self.game_menu
        self.game_menu_button.grid(sticky="nw", column=0, row=3, padx=3, pady=3)

        self.selected_game_name.trace_add('write', self.selected_game_callback)

        self.sort_menu_button = Menubutton(self.app_frame_left_0, width=18, text='Sort By Number')
        self.sort_menu = Menu(self.sort_menu_button, tearoff=0)
        self.sort_menu.add_radiobutton(
            label="Sort By Number",
            value=0,
            variable=self.selected_sort
        )
        self.sort_menu.add_radiobutton(
            label="Sort By Name",
            value=1,
            variable=self.selected_sort
        )

        self.sort_menu.configure()
        self.sort_menu_button["menu"] = self.sort_menu
        self.sort_menu_button.grid(sticky="nw", column=1, row=3, padx=(5,3), pady=3)

        self.selected_sort.trace_add('write', self.selected_sort_callback)


    def selected_game_callback(self, var_name, index, mode):
        new_game = self.selected_game_name.get()
        self.game_menu_button.config(text=new_game)

        with open(os.path.join(self.games_dir, new_game + ".csv"), newline='') as csvfile:
            lamps = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
            self.manu_id.set(Manu_String_to_ID[lamps[0][0].upper()])
            self.name_dict = {}
            for row in lamps:
                try:
                    self.name_dict.update({int(row[0]): row[1].strip()})
                except:
                    pass

        self.draw_lamp_rows()


    def draw_lamp_rows(self):
        sort_by = self.selected_sort.get()
        if sort_by == 0:
            self.name_dict = dict(sorted(self.name_dict.items(), reverse=self.reverse_sort))
        else:
            self.name_dict = dict(sorted(self.name_dict.items(), key=lambda item: item[1], reverse=self.reverse_sort))

        self.last_sort = sort_by

        for x in self.grid_items:
            x.grid_forget()

        self.grid_items = []

        row = 0
        for lnum in self.name_dict:
            row = row + 1
            var_name = "Lamp{:02d}".format(lnum)
            
            self.lamp_num_labels_dict[var_name].grid(sticky="nsew", column=0, row=row, pady=2)
            self.grid_items.append(self.lamp_num_labels_dict[var_name])

            self.lamp_name_labels_dict[var_name].config(text = "{:<38s}".format(self.name_dict[lnum]))
            self.lamp_name_labels_dict[var_name].grid(sticky="nsew", column=1, row=row, padx=2, pady=2)
            self.grid_items.append(self.lamp_name_labels_dict[var_name])

            pnum = self.settings["lamp_vars"][lnum-1].get()
            self.lamp_profile_name_labels_dict[var_name].config(textvariable=self.settings["profile_vars"][pnum-1]["name"])
            self.lamp_profile_name_labels_dict[var_name].grid(sticky="nsew", column=2, row=row, padx=2, pady=2)
            self.grid_items.append(self.lamp_profile_name_labels_dict[var_name])

            self.lamp_menu_buttons_dict[var_name].grid(sticky="nsew", column=3, row=row, pady=2, ipady=0)
            self.grid_items.append(self.lamp_menu_buttons_dict[var_name])

        self.app_frame_left_1.update() # update rfbc_frame height so it's no longer 0 ( height is 0 when it has just been created )
        self.app_frame_left_1.configure()

        self.manual_lamp_menu.delete(0, "end")
        for lnum in self.name_dict:
            lamp_menu_str = "{:02d}: {:s}".format(lnum, self.name_dict[lnum])
            self.manual_lamp_menu.add_radiobutton(
                label=lamp_menu_str,
                value=lnum,
                variable=self.selected_manual_lamp
            )

        sel_lamp = self.selected_manual_lamp.get()
        if sel_lamp:
            if sel_lamp in self.name_dict:
                selected_lnum = sel_lamp
                self.manual_lamp_menu_button.config(text="{:02d}: {:<38s}".format(selected_lnum, self.name_dict[selected_lnum]))
            else:
                self.selected_manual_lamp.set(False)
                self.manual_lamp_menu_button.config(text="{:<42s}".format("Lamp"))

        self.manual_lamp_menu.configure()


    def selected_sort_callback(self, var_name, index, mode):
        sort_by = self.selected_sort.get()

        if sort_by == self.last_sort:
            self.reverse_sort = not self.reverse_sort
        self.last_sort = sort_by

        new_text = ("Sort " + ("By Name" if sort_by == 1 else "By Number") + (" Reversed" if self.reverse_sort else ""))
        self.sort_menu_button.config(text=new_text)

        self.draw_lamp_rows()


    def build_lamp_matrix(self):
        profiles_vars = []

        Label(self.app_frame_right_1, text="Min", justify="left").grid(sticky="ns", column = 3, row = 0)
        Label(self.app_frame_right_1, text="Brightnesses", justify="right", font="-size 10 -weight bold").grid(sticky="ns", column = 4, row = 0, columnspan=3)
        
        self.advanced = BooleanVar(value=False)
        self.advanced_toggle = Checkbutton(self.app_frame_right_1, text="Advanced", variable=self.advanced, bootstyle="square toggle", )
        self.advanced_toggle.grid(sticky="ns", column=6, columnspan=4, row=0, padx=3, pady=3)
        self.gui_when_connected.append(self.advanced_toggle)
        self.advanced.trace_add('write', self.advanced_set_callback)

        Label(self.app_frame_right_1, text="Max", justify="left").grid(sticky="ns", column = 10, row = 0)

        Label(self.app_frame_right_1, text="#", justify="left").grid(sticky="ns", column = 0, row = 1)
        Label(self.app_frame_right_1, text="Profile Name", justify="left").grid(sticky="ns", column = 2, row = 1)
        Label(self.app_frame_right_1, text="Delay", justify="left").grid(sticky="ns", column = 11, row = 1, columnspan=2)

        for pnum in range (0, 8):
            Label(self.app_frame_right_1, text=f"B{pnum+1}", justify="left", width=2).grid(column = pnum+3, row = 1)
            Label(self.app_frame_right_1, text=pnum+1, justify="left", width=1).grid(sticky="ns", column = 0, row = pnum+3)

            curr_var_set = {}
            
            pname = f"Profile{pnum+1}"

            # ex: "Profile3_Name" with value "LED 35%"
            curr_var = StringVar(self.app, name=pname + "_Name", value="")
            curr_var_set.update({"name": curr_var})
            curr_widget = Entry(self.app_frame_right_1, text="", textvariable=curr_var, width=8, justify="left", takefocus=True, validate="key", validatecommand=(self.val_text, "%P", 8))
            curr_widget.grid(sticky="ns", column = 2, row = pnum+3, padx=3, pady=3)
            self.gui_when_connected.append(curr_widget)
            self.gui_in_normal.append(curr_widget)

            # ex: "Profile7_Bright3" with value 30
            curr_brightness_vars = []
            for bnum in range (0, 8):
                curr_var = IntVar(self.app, name=pname + f"_Bright{bnum+1}", value = 0)
                if bnum == 0 or bnum == 7:
                    curr_var.trace_add("write", self.on_brightness)

                curr_brightness_vars.append(curr_var)
                curr_widget = Entry(self.app_frame_right_1, text="", textvariable=curr_var, width=3, justify="left", takefocus=True, state="disabled" if (bnum>=1 and bnum <= 6) else "normal", validate="key", validatecommand=(self.val_num, "%P", 0, 100))
                curr_widget.bind("<FocusOut>", self.focus_out_profiles)
                self.gui_when_connected.append(curr_widget)
                self.gui_in_normal.append(curr_widget)

                if bnum>=1 and bnum <= 6:
                    self.gui_in_advanced.append(curr_widget)

                curr_widget.grid(sticky="ns", column = bnum+3, row = pnum+3, padx=3, pady=3)

            curr_var_set.update({"brightnesses": curr_brightness_vars})

            # ex: "Profile1_Delay" with value 3
            curr_var = IntVar(self.app, name=pname + "_Delay", value = 0)
            curr_var_set.update({"delay": curr_var})

            curr_widget = Entry(self.app_frame_right_1, text="", textvariable=curr_var, width=2, justify="left", takefocus=True, validate="key", validatecommand=(self.val_num, "%P", 0, 99))
            curr_widget.bind("<FocusOut>", self.focus_out_profiles)
            curr_widget.grid(sticky="ns", column = 11, row = pnum+3, padx=3, pady=3)
            self.gui_when_connected.append(curr_widget)
            self.gui_in_normal.append(curr_widget)
            profiles_vars.append(curr_var_set)
        
        self.settings.update({"profile_vars": profiles_vars})


    def on_brightness(self, var_name, index, mode):
        if not self.advanced.get():
            pnum = int(var_name[7])

            try:
                min = self.settings["profile_vars"][pnum-1]["brightnesses"][0].get()
                max = self.settings["profile_vars"][pnum-1]["brightnesses"][7].get()

                if min <= max:
                    dist_nums = gen_nums (min, max, 8)
                    for x in range(1, 7):
                        self.settings["profile_vars"][pnum-1]["brightnesses"][x].set(dist_nums[x])
            except:
                pass


    def advanced_set_callback(self, var_name, index, mode):
        if self.advanced.get():
            if self.manual_mode:
                for x in self.gui_in_manual_advanced:
                    x.configure(state="!disabled", takefocus=True)
                for x in self.gui_in_advanced:
                    x.configure(state="disabled", takefocus=False)
            else:
                for x in self.gui_in_manual_advanced:
                    x.configure(state="disabled", takefocus=False)
                for x in self.gui_in_advanced:
                    x.configure(state="!disabled", takefocus=True)
        else:
            for x in self.gui_in_manual_advanced:
                x.configure(state="disabled", takefocus=False)
            for x in self.gui_in_advanced:
                x.configure(state="disabled", takefocus=False)


    def focus_out_profiles(self, event):
        var_name = event.widget.cget("textvariable")
        pnum = int(var_name[7])

        if var_name[9:] == "Delay":
            try:
                val = self.settings["profile_vars"][pnum-1]["delay"].get()
            except:
                self.settings["profile_vars"][pnum-1]["delay"].set(0)
        else:
            bnum = int(var_name[15])
            try:
                val = self.settings["profile_vars"][pnum-1]["brightnesses"][bnum-1].get()
            except:
                self.settings["profile_vars"][pnum-1]["brightnesses"][bnum-1].set(0)


    def build_lamp_menu(self):
        for lnum in range(1, 89):
            var_name = "Lamp{:02d}".format(lnum)

            self.lamp_num_labels_dict.update({var_name: Label(self.app_frame_left_1, text=f"{lnum:02d}", font=("Monaco", 10), padding=(3, 3), background="gray90")})
            self.lamp_name_labels_dict.update({var_name: Label(self.app_frame_left_1, text=var_name, font=("Monaco", 10), padding=(3, 3), background="gray90")})
            self.lamp_profile_name_labels_dict.update({var_name: Label(self.app_frame_left_1, text=var_name, width=8, textvariable=self.settings["profile_vars"][6]["name"], font=("Monaco", 10), padding=(3, 3), background="gray90")})

            self.settings["lamp_vars"][lnum-1].set(7)

            self.lamp_menu_buttons_dict.update({var_name: Menubutton(self.app_frame_left_1, text='7')})
            self.gui_when_connected.append(self.lamp_menu_buttons_dict[var_name])
            self.gui_in_normal.append(self.lamp_menu_buttons_dict[var_name])

            self.settings["lamp_vars"][lnum-1].trace_add(
                'write', self.lamp_var_callback
            )

            self.lamp_menus_list.append(Menu(self.lamp_menu_buttons_dict[var_name], tearoff=0))
            for y in range(1, 9):
                self.lamp_menus_list[-1].add_radiobutton(
                    label=y,
                    value=y,
                    variable=self.settings["lamp_vars"][lnum-1]
                )
            self.lamp_menus_list[-1].configure()
            self.lamp_menu_buttons_dict[var_name]["menu"] = self.lamp_menus_list[-1]
        self.app_frame_left_1.update()  # update rfbc_frame height so it's no longer 0 ( height is 0 when it has just been created )
                                        # in this case "x=0 y=0 width=0 height=rfbc_frame height"
                                        # width 0 because we only scroll verticaly so don't mind about the width.

        self.app_frame_left_1.configure()


    def lamp_var_callback(self, var_name, index, mode):
        lnum = int(var_name[-2:])
        value = self.settings["lamp_vars"][lnum-1].get()
        self.lamp_menu_buttons_dict[var_name].config(text=value)
        self.lamp_profile_name_labels_dict[var_name].config(textvariable=self.settings["profile_vars"][value-1]["name"])


    def build_manual_widgets(self):
        # Build the lamp selection menu
        self.manual_window_width = 550
        self.manual_window_height = 395
        self.manual_window = Toplevel(master=self.app, title="Manual Mode", size=(self.manual_window_width, self.manual_window_height), topmost=True)
        self.manual_window.resizable(False, False)
        self.manual_window.on_close(self.manual_close)
        self.manual_window.withdraw()

        self.manual_window_frame_0 = Frame(self.manual_window)
        self.manual_window_frame_0.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        self.manual_window_frame_1 = Frame(self.manual_window)
        self.manual_window_frame_1.grid(sticky="nsew", column=0, row=1, padx=3, pady=(20,3))

        self.manual_window_frame_2 = Frame(self.manual_window)
        self.manual_window_frame_2.grid(sticky="nsew", column=0, row=2, padx=(85,3), pady=((20,3)))

        self.manual_window_frame_3 = Frame(self.manual_window)
        self.manual_window_frame_3.grid(sticky="nsew", column=0, row=3, padx=(85,3), pady=(0,3))

        self.manual_window_frame_4 = Frame(self.manual_window)
        self.manual_window_frame_4.grid(sticky="nsew", column=0, row=4, padx=3, pady=3)
        
        self.manual_window_frame_5 = Frame(self.manual_window)
        self.manual_window_frame_5.grid(sticky="nsew", column=0, row=5, padx=3, pady=3)

        instructions = Text(self.manual_window, width=55, height=8, font = ("Arial", 12), wrap="word")
        instructions.insert("end", '''Manual Mode is used to test lamps you choose with different brightnesses. To begin set the brightness values for B1 to B8 below if desired, then select a lamp and a brightness from the menus and click the "Send" button to light the lamp with that brightness number. Repeat for other lamps.

If you wish to keep the brightness values B1 to B8, select a Profile to save the settings to and click the "Keep" button. To reject the changes click the "Cancel" button or close the window.''')
        instructions.configure(state="disabled")          
        instructions.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)

        self.manual_lamp_menu_button = Menubutton(self.manual_window_frame_1, text="Lamp", width=30)
        self.manual_lamp_menu = Menu(self.manual_lamp_menu_button, tearoff=0)
        for lnum in self.name_dict:
            lamp_menu_str = "{:02d}: {:<38s}".format(lnum, self.name_dict[lnum])
            self.manual_lamp_menu.add_radiobutton(
                label=lamp_menu_str,
                value=lnum,
                variable=self.selected_manual_lamp
            )
        self.manual_lamp_menu.configure()
        self.manual_lamp_menu_button["menu"] = self.manual_lamp_menu
        self.manual_lamp_menu_button.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)
        self.gui_in_manual.append(self.manual_lamp_menu_button)

        self.selected_manual_lamp.trace_add('write', self.manual_lamp_callback)

        self.manual_bright_menu_button = Menubutton(self.manual_window_frame_1, text = "Bright", width=6)
        self.manual_bright_menu = Menu(self.manual_bright_menu_button, tearoff=0)

        for bnum in range(1, 9):
            bmenu_str = f"B{bnum}"
            self.manual_bright_menu.add_radiobutton(
                label=bmenu_str,
                value=bnum,
                variable=self.selected_brightnesss_num
            )
        self.manual_bright_menu.configure()
        self.manual_bright_menu_button["menu"] = self.manual_bright_menu
        self.manual_bright_menu_button.grid(sticky="nw", column=2, row=0, padx=3, pady=3)
        self.gui_in_manual.append(self.manual_bright_menu_button)

        self.selected_brightnesss_num.trace_add('write', self.manual_brightness_callback)

        self.manual_send_button = Button(self.manual_window_frame_1, text = "Send", width=4, command=self.ManualSendButtonClicked)
        self.manual_send_button.grid(sticky="nsew", column=3, row=0, padx=3, pady=3)

        self.manual_reset_button = Button(self.manual_window_frame_1, text = "Reset", width=4, command=self.ManualResetButtonClicked)
        self.manual_reset_button.grid(sticky="nsew", column=4, row=0, padx=3, pady=3)

        self.manual_advanced_toggle = Checkbutton(self.manual_window_frame_2, text="Advanced", variable=self.advanced, bootstyle="square toggle")
        self.manual_advanced_toggle.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)
        self.gui_in_manual.append(self.manual_advanced_toggle)

        self.manual_brightness_vars = []
        bvals = gen_nums(20, 100, 8)
        for bnum in range (0, 8):
            curr_label = Label(self.manual_window_frame_3, text=f"B{bnum+1}", justify="left", width=2).grid(column = bnum, row = 0, padx=3, pady=3)
            ToolTip(curr_label, text=f"Brightness {bnum+1}")
            curr_var = IntVar(self.app, name=f"Manual_Bright{bnum+1}", value = bvals[bnum])
            if bnum == 0 or bnum == 7:
                curr_var.trace_add("write", self.on_manual_brightness)

            self.manual_brightness_vars.append(curr_var)
            curr_widget = Entry(self.manual_window_frame_3, text="", textvariable=curr_var, width=3, justify="left", takefocus=True, state="disabled", validate="key", validatecommand=(self.val_num, "%P", 0, 100))

            self.gui_in_manual.append(curr_label)
            self.gui_in_manual.append(curr_widget)

            if bnum>=1 and bnum <= 6:
                self.gui_in_manual_advanced.append(curr_widget)
                curr_widget.state(["disabled"])

            curr_widget.grid(sticky="nsew", column = bnum, row = 1, padx=3, pady=3)

        self.normalocd_button = Button(self.manual_window_frame_5, text="Cancel", command=self.manual_cancel_button_clicked)
        self.normalocd_button.grid(sticky="nsew", column=0, row=0, padx=(120,40), pady=3)
        self.gui_when_connected.append(self.normalocd_button)
        self.gui_in_manual.append(self.normalocd_button)

        self.manual_profile_menu_button = Menubutton(self.manual_window_frame_5, text = "Select Profile", width=10)
        self.manual_profile_menu = Menu(self.manual_profile_menu_button, tearoff=0)

        for pnum in range(1, 9):
            pmenu_str = f"Profile {pnum}"
            self.manual_profile_menu.add_radiobutton(
                label=pmenu_str,
                value=pnum,
                variable=self.selected_keep_profile_num
            )
        self.manual_profile_menu.configure()
        self.manual_profile_menu_button["menu"] = self.manual_profile_menu
        self.manual_profile_menu_button.grid(sticky="nsew", column=1, row=0, padx=3, pady=3)
        self.gui_in_manual.append(self.manual_profile_menu_button)

        self.selected_keep_profile_num.trace_add('write', self.manual_profile_callback)

        self.keep_button = Button(self.manual_window_frame_5, text = "Keep", state="disabled", command=self.KeepButtonClicked)
        self.keep_button.grid(sticky="nsew", column=2, row=0, padx=3, pady=3)

        self.manual_window.update()


    def manual_close(self):
        for bnum in range(1,9):
            if not self.led_ocd.SendSetPBCmd(pnum = 7, brightnum = bnum, value = self.saved_profile_7_brightnesses[bnum-1]):
                self.result.set("ERROR: Could not restore profile 7 brightnesses! Try again and if it fails quit this tool and power cycle the pinball machine to restore the settings.")
                return False
            
        self.selected_manual_lamp.set(False)
        self.selected_brightnesss_num.set(False)
        self.selected_keep_profile_num.set(False)
        self.manual_lamp_menu_button.config(text="{:<42s}".format("Lamp"))

        self.manual_mode = False
        self.manual_window.withdraw()

        self.NormalButtonClicked()
        return True
    

    def manual_cancel_button_clicked(self):
        self.NormalButtonClicked()
        self.manual_window.withdraw()


    def on_manual_brightness(self, var_name, index, mode):
        if not self.advanced.get():
            try:
                min = self.manual_brightness_vars[0].get()
                max = self.manual_brightness_vars[7].get()

                if min <= max:
                    dist_nums = gen_nums (min, max, 8)
                    for x in range(1, 7):
                        self.manual_brightness_vars[x].set(dist_nums[x])
            except:
                pass


    def manual_lamp_callback(self, var_name, index, mode):
        lnum = self.selected_manual_lamp.get()
        if lnum:
            self.manual_lamp_menu_button.config(text="{:02d}: {:<38s}".format(lnum, self.name_dict[lnum]))
        else:
            self.manual_profile_menu_button.config(text="Select Profile")
        

    def manual_brightness_callback(self, var_name, index, mode):
        bnum = self.selected_brightnesss_num.get()
        if bnum:
            self.manual_bright_menu_button.config(text=f"B{bnum}")
        else:
            self.manual_bright_menu_button.config(text="Bright")
        

    def manual_profile_callback(self, var_name, index, mode):
        pnum = self.selected_keep_profile_num.get()
        if pnum:
            self.manual_profile_menu_button.config(text = f"Profile {pnum}     ")
            self.keep_button.configure(state = "!disabled")
        else:
            self.manual_profile_menu_button.config(text = f"Select Profile")
            self.keep_button.configure(state = "disabled")
        

    def load_from_xml_file(self, xml_filepath):
        try:
            tree = ET.parse(xml_filepath)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"XML file not found: {xml_filepath}") from exc
        
        root = tree.getroot()

        gname = root.findtext("title")
        if gname:
            game_file = os.path.join(self.games_dir, f"{gname}.csv")

        if game_file and os.path.exists(game_file):
            self.game_file = game_file
            file_found = False
            gfile = os.path.basename(game_file)
            pattern = r".*\.csv$"
            
            for f in os.listdir(self.games_dir):
                if (not file_found) and re.search(pattern, f):
                    if f == gfile:
                        file_found = True
                        game = os.path.splitext(gfile)[0]
                        self.selected_game_name.set(game)
                        with open(os.path.join(self.games_dir, gfile), newline='') as csvfile:
                            lamps = list(csv.reader(csvfile, delimiter=',', quotechar='|'))
                            self.manu_id.set(Manu_String_to_ID[lamps[0][0].upper()])

            if not file_found:
                match self.manu_id.get():
                    case Manufacturers.STERN:
                        self.selected_game_name.set(DEFAULT_STERN_GAME)
                    case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                        self.selected_game_name.set(DEFAULT_WPC_GAME)
                    case _:
                        self.manu_id.set(Manufacturers.WPC)
                        self.selected_game_name.set(DEFAULT_WPC_GAME)
        else:
            match self.manu_id.get():
                case Manufacturers.STERN:
                    self.selected_game_name.set(DEFAULT_STERN_GAME)
                case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                    self.selected_game_name.set(DEFAULT_WPC_GAME)
                case _:
                    self.manu_id.set(Manufacturers.WPC)
                    self.selected_game_name.set(DEFAULT_WPC_GAME)

        advanced = root.findtext("advanced").lower() == "true"
        self.advanced.set(advanced)

        cnt = 0
        for lnum in range(1, 89):
            profile = root.findtext("lamp{:02d}/profile".format(lnum))
            if profile:
                self.settings["lamp_vars"][lnum-1].set(int(profile))
                cnt += 1

        for pnum in range(1, 9):
            pname = root.findtext("profile{}/name".format(pnum))
            if pname:
                self.settings["profile_vars"][pnum-1]["name"].set(pname)
                cnt += 1
            delay = root.findtext("profile{}/delay".format(pnum))
            if delay:
                self.settings["profile_vars"][pnum-1]["delay"].set(delay)
                cnt += 1
            for bnum in range(1, 9):
                bval = root.findtext("profile{}/b{}".format(pnum, bnum))
                if bval:
                    self.settings["profile_vars"][pnum-1]["brightnesses"][bnum-1].set(bval)
                    cnt += 1

        if cnt == SETTINGS_OBJ_CNT or cnt == SETTINGS_OBJ_CNT_WPC or cnt == SETTINGS_OBJ_CNT_STERN:
            return True
        else:
            return False


    def save_to_xml_file(self, xml_file):
        if self.progress_window:
            prog = self.progress.get()
            self.set_progress_title("Exporting to XML...")
        else:
            self.open_progress("Saving to XML...")
            self.progress.set(0)
            prog = 0

        increment = (100-prog)/SETTINGS_OBJ_CNT

        declaration = '<?xml version="1.0" encoding="utf-8"?>\n'

        root = ET.Element("settings")

        name_e = ET.Element("title")
        name_e.text = self.selected_game_name.get()
        root.append(name_e)

        advanced_e = ET.Element("advanced")
        advanced_e.text = "true" if self.advanced.get() else "false"
        root.append(advanced_e)

        for lnum in self.name_dict:
            curr_lamp_e = ET.Element("lamp{:02d}".format(lnum))
            root.append(curr_lamp_e)

            curr_profile_se = ET.SubElement(curr_lamp_e, "profile")
            curr_profile_se.text = "{:d}".format(self.settings["lamp_vars"][lnum-1].get())
            prog += increment
            self.set_progress(prog)

        for pnum in range(1, 9):
            curr_prof_e = ET.Element(f"profile{pnum}")
            root.append(curr_prof_e)

            curr_prof_name_e = ET.SubElement(curr_prof_e, "name")
            curr_prof_name_e.text = self.settings["profile_vars"][pnum-1]["name"].get()
            prog += increment
            self.set_progress(prog)

            for bnum in range(1, 9):
                curr_b_e = ET.SubElement(curr_prof_e, f"b{bnum}")
                curr_b_e.text = "{:d}".format(self.settings["profile_vars"][pnum-1]["brightnesses"][bnum-1].get())
                prog += increment
                self.set_progress(prog)

            curr_prof_delay_e = ET.SubElement(curr_prof_e, "delay")
            curr_prof_delay_e.text = "{:d}".format(self.settings["profile_vars"][pnum-1]["delay"].get())
            prog += increment
            self.set_progress(prog)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)

        with open (xml_file, "wb") as f:
            f.write(declaration.encode("utf-8"))
            tree.write(f, encoding="utf-8")

        self.close_progress()

        return True


    def load_from_json_file(self, json_filename):
        imported_settings = self.led_ocd.FromJSON(json_filename)

        if imported_settings:
            for x in imported_settings:
                if isinstance(x, LampProfile):
                    self.settings["lamp_vars"][x.lamp_num-1].set(x.profile_num)
                elif isinstance(x, ProfileName):
                    self.settings["profile_vars"][x.profile_num-1]["name"].set(x.name)
                elif isinstance(x, ProfileDelay):
                    self.settings["profile_vars"][x.profile_num-1]["delay"].set(x.delay)
                elif isinstance(x, ProfileBrightnessPercent):
                    self.settings["profile_vars"][x.profile_num-1]["brightnesses"][x.brightness_num-1].set(x.percent)
            self.result.set(f"Settings imported from {json_filename}")
            return True
        else:
            self.result.set(f"ERROR: Settings could not be imported from {json_filename}")
            return False


    def save_to_json_file(self, json_file):
        json_data = self.led_ocd.ToJSON()
        if json_data:
            with open(json_file, "w") as f:
                f.write(json_data)
            return True
        else:
            return False


    def backup(self, tag=None, game_name=None):
        if game_name is None:
            game_name = self.selected_game_name.get()
        if tag:
            backup_name = '{} {} - {date:%Y-%m-%d %H-%M-%S}.xml'.format(game_name, tag, date=datetime.datetime.now())
        else:
            backup_name = '{} - {date:%Y-%m-%d %H-%M-%S}.xml'.format(game_name, date=datetime.datetime.now())

        bkup_path = os.path.join(self.backups_dir, backup_name)

        if self.save_to_xml_file(bkup_path):
            backup_limit = self.options["backups"]["limit_to"].get()
            if backup_limit > 0:
                pattern = os.path.join(self.backups_dir, f"{game_name}*.xml")
                backup_files = sorted(glob.glob(pattern), key=os.path.getctime)
                num_bkups = len(backup_files)
                if num_bkups > backup_limit:
                    for f in backup_files[:(num_bkups-backup_limit)]:
                        os.remove(f)
            self.result.set(f"Settings backed up in \"{backup_name}\"")
        else:
            self.result.set(f"WARNING: Settings could not be backed up")


    def update_uledocd(self):
        new_settings = []

        match self.manu_id.get():
            case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                lamp_numbers = [x for x in range(11, 89) if x%10 >= 1 and x%10 <= 8]
            case Manufacturers.STERN:
                lamp_numbers = range(1, 81)
            case _:
                return False
            
        for lnum in lamp_numbers:
            pnum = self.settings["lamp_vars"][lnum-1].get()
            if pnum:
                new_settings.append(LampProfile(lamp_num = lnum, profile_num=pnum))

        for pnum in range(1, 9):
            pname = self.settings["profile_vars"][pnum-1]["name"].get()
            new_settings.append(ProfileName(profile_num=pnum, name=pname))

            pdelay = self.settings["profile_vars"][pnum-1]["delay"].get()
            new_settings.append(ProfileDelay(profile_num=pnum, delay=pdelay))

            for bnum in range(1, 9):
                bpercent = self.settings["profile_vars"][pnum-1]["brightnesses"][bnum-1].get()
                new_settings.append(ProfileBrightnessPercent(profile_num=pnum, brightness_num=bnum, percent=bpercent))

        if self.led_ocd.UpdateSettings(self.manu_id.get(), new_settings):
            return True
        else:
            self.result.set(f"ERROR: one or more of the settings were invalid or the number of settings {len(new_settings)} was invalid")
            return False


    def show_options(self):
        options_width = 326
        options_height = 390
        self.options_window = Toplevel(master=self.app, title="Options", size=(options_width, options_height), topmost=True, transient=self.app, resizable=(False, False))
        self.options_window.on_close(self.options_closed_callback)

        x = self.app.winfo_x() + self.app.winfo_width()//2 - options_width//2
        y = self.app.winfo_y() + self.app.winfo_height()//2 - options_height//2
        self.options_window.geometry(f"+{x}+{y}")

        options_window_frame_0 = Frame(self.options_window, bootstyle="@card")
        options_window_frame_0.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)

        options_label_1 = Label(options_window_frame_0, text="Startup Options", font="-size 12 -weight bold", bootstyle="@card")
        options_label_1.grid(sticky="nsew", column=0, row=0, columnspan=2, padx=3, pady=3)

        options_window_frame_1 = Frame(self.options_window, bootstyle="@card")
        options_window_frame_1.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        options_label_2 = Label(options_window_frame_1, text="Backup Options", font="-size 12 -weight bold", bootstyle="@card")
        options_label_2.grid(sticky="nsew", column=0, row=0, columnspan=2, padx=3, pady=3)

        options_window_frame_2 = Frame(self.options_window, bootstyle="@card")
        options_window_frame_2.grid(sticky="nsew", column=0, row=2, padx=3, pady=3)

        options_label_3 = Label(options_window_frame_2, text="Other Options", font="-size 12 -weight bold", bootstyle="@card")
        options_label_3.grid(sticky="nsew", column=0, row=0, columnspan=2, padx=3, pady=3)

        options_window_frame_3 = Frame(self.options_window, bootstyle="@card")
        options_window_frame_3.grid(sticky="nsew", column=0, row=3, padx=3, pady=3)

        options_cancel_btn = Button(options_window_frame_3, text="Cancel", command=self.options_cancel_button_clicked)
        options_cancel_btn.grid(sticky="nsew", column=0, row=0, padx=(90,3), pady=3)
        options_apply_btn = Button(options_window_frame_3, text="Apply", command=self.options_apply_button_clicked)
        options_apply_btn.grid(sticky="nsew", column=1, row=0, padx=3, pady=3)

        self.new_options = self.copy_options(self.options)

        # Startup Options
        select_last_game_btn = Checkbutton(options_window_frame_0, text="Select Last Game", variable=self.new_options["on_startup"]["select_last_game"], bootstyle="square toggle")
        ToolTip(select_last_game_btn, text="If enabled, on startup select the last game that was selected")
        select_last_game_btn.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        select_last_port_btn = Checkbutton(options_window_frame_0, text="Select Last Successful Port", variable=self.new_options["on_startup"]["select_last_port"], bootstyle="square toggle")
        ToolTip(select_last_port_btn, text="If enabled, on startup select the last port that was sucessfully connected to, if that port is available")
        select_last_port_btn.grid(sticky="nsew", column=0, row=2, padx=3, pady=3)

        import_last_backup_btn = Checkbutton(options_window_frame_0, text="Import Last Backup", variable=self.new_options["on_startup"]["import_last_backup"], bootstyle="square toggle")
        ToolTip(import_last_backup_btn, text="If enabled, on startup import the last backup - this overrides the Select Last Game option unless no backups exist")
        import_last_backup_btn.grid(sticky="nsew", column=0, row=3, padx=3, pady=3)

        # Backup Options
        on_read_btn = Checkbutton(options_window_frame_1, text="Backup After Read", variable=self.new_options["backups"]["on_read"], bootstyle="square toggle")
        ToolTip(on_read_btn, text="If enabled a backup will be made every time settings are read from the LED OCD board")
        on_read_btn.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        on_send_btn = Checkbutton(options_window_frame_1, text="Backup After Send", variable=self.new_options["backups"]["on_send"], bootstyle="square toggle")
        ToolTip(on_send_btn, text="If enabled a backup will be made every time settings are sent to the LED OCD board")
        on_send_btn.grid(sticky="nsew", column=0, row=2, padx=3, pady=3)

        tooltip = "Limit the number of backups per game to this value. If at the limit, a new backup is made and the oldest backups for that game are deleted until only the set number of backups remain for that game"
        limit_to_label = Label(options_window_frame_1, text="Number Of Backups Per Game:", bootstyle="@card")
        ToolTip(limit_to_label, text=tooltip)
        limit_to_label.grid(sticky="nsew", column=0, row=3, padx=3, pady=3)
        limit_to_sb = Spinbox(options_window_frame_1, from_=0, to=1000000, increment=1, width=7, textvariable=self.new_options["backups"]["limit_to"])
        ToolTip(limit_to_sb, text=tooltip)
        limit_to_sb.grid(sticky="nsw", column=1, row=3, padx=3, pady=3)

        # Other Options
        verify_sends_btn = Checkbutton(options_window_frame_2, text="Verify Sends", variable=self.new_options["other"]["verify_sends"], bootstyle="square toggle")
        ToolTip(verify_sends_btn, text="If this is enabled, verify after sending settings to the LED OCD board that the settings on the board match the settings sent")
        verify_sends_btn.grid(sticky="nsew", column=0, row=1, padx=3, pady=3)

        self.options_window.grab_set()
        self.options_window.update()
        self.app.wait_window(self.options_window)
        self.options_window = None
        return True


    def copy_options(self, from_options):
        to_options = None
        to_options = {
            "on_startup": {
                "select_last_game": BooleanVar(value=from_options["on_startup"]["select_last_game"].get()),
                "import_last_backup": BooleanVar(value=from_options["on_startup"]["import_last_backup"].get()),
                "select_last_port": BooleanVar(value=from_options["on_startup"]["select_last_port"].get()),
            },
            "backups": {
                "on_read": BooleanVar(value=from_options["backups"]["on_read"].get()),
                "on_send": BooleanVar(value=from_options["backups"]["on_send"].get()),
                "limit_to": IntVar(value=from_options["backups"]["limit_to"].get()),
            },
            "other": {
                "verify_sends": BooleanVar(value=from_options["other"]["verify_sends"].get()),
            }
        }
        return to_options


    def options_cancel_button_clicked(self):
        self.options_window.destroy()

    def options_apply_button_clicked(self):
        self.options = self.copy_options(self.new_options)
        self.save_options()
        self.result.set("Options changes applied and saved")
        self.options_window.destroy()

    def options_closed_callback(self):
        result = Messagebox.okcancel("Save the options?", buttons=("Cancel", "Don't Apply", "Apply"))
        if result == "Apply":
            self.options = self.copy_options(self.new_options)
            self.save_options()
            self.result.set("Options changes applied and saved")
        if result == "Cancel":
            return False
        else:
            return True

    # Functions for user buttons
    def ConnectButtonClicked(self):
        self.open_progress("Connecting...")

        ocd_port = self.selected_port.get()
        try:
            self.led_ocd.SetPort(ocd_port)
            self.led_ocd.Connect()
        except serial.serialutil.SerialException:
            self.result.set(f"ERROR: Could not connect to {ocd_port}")
            return False

        self.set_progress(25)

        for x in self.gui_when_connected:
            x.state(["!disabled"])

        for x in self.gui_when_disconnected:
            x.state(["disabled"])

        for x in self.gui_in_manual:
            x.state(["disabled"])

        if not self.advanced.get():
            for x in self.gui_in_advanced:
                x.configure(state="disabled", takefocus=False)
            for x in self.gui_in_manual_advanced:
                x.configure(state="disabled", takefocus=False)

        self.set_progress(50)

        try:
            version = self.led_ocd.SendVersionCmd()[1]
            if version:
                self.data["last_port"] = self.selected_port.get()
                self.save_data()
                self.result.set(f"Connected to {ocd_port}")
                self.result.set(f"{version}")
                self.set_progress(100)
                self.close_progress()
                return True
            else:
                self.DisconnectButtonClicked()
                self.result.set(f"ERROR: Connected to {ocd_port}, but could not retrieve LED OCD version! Disconnecting.")
                self.set_progress(100)
                self.close_progress()
                return False
        except:
            self.DisconnectButtonClicked()
            self.result.set(f"ERROR: Failed to connect to {ocd_port}")
            self.set_progress(100)
            self.close_progress()
            return False


    def DisconnectButtonClicked(self):
        self.NormalButtonClicked()
        self.led_ocd.Disconnect()

        self.manual_mode = False

        for x in self.gui_when_connected:
            x.state(["disabled"])

        for x in self.gui_when_disconnected:
            x.state(["!disabled"])

        for x in self.gui_in_manual:
            x.state(["disabled"])

        self.result.set("Disconnected")


    def ReadButtonClicked(self):
        self.open_progress("Reading settings...")

        read_settings = self.led_ocd.SendReadSettingsCmd()[1]

        self.set_progress(10)

        cnt = 0
        if read_settings:
            num_settings = len(read_settings)
            if self.options["backups"]["on_read"].get():
                increment = 50/num_settings
            else:
                increment = 90/num_settings
            prog = 10

            for x in read_settings:
                if isinstance(x, LampProfile):
                    self.settings["lamp_vars"][x.lamp_num-1].set(x.profile_num)
                    cnt += 1
                elif isinstance(x, ProfileName):
                    self.settings["profile_vars"][x.profile_num-1]["name"].set(x.name)
                    cnt += 1
                elif isinstance(x, ProfileDelay):
                    self.settings["profile_vars"][x.profile_num-1]["delay"].set(x.delay)
                    cnt += 1
                elif isinstance(x, ProfileBrightnessPercent):
                    self.settings["profile_vars"][x.profile_num-1]["brightnesses"][x.brightness_num-1].set(x.percent)
                    cnt += 1

                prog += increment
                self.set_progress(prog)

            if cnt == SETTINGS_OBJ_CNT or cnt == SETTINGS_OBJ_CNT_STERN or cnt == SETTINGS_OBJ_CNT_WPC:
                if self.options["backups"]["on_read"].get():
                    self.result.set("Settings successfully read")
                    self.backup(tag="READ")
                rtn_val = True
            else:
                self.result.set(f"ERROR: Incorrect number of settings read ({cnt}) from the LED OCD board (should be {SETTINGS_OBJ_CNT_WPC}, {SETTINGS_OBJ_CNT_STERN} or {SETTINGS_OBJ_CNT})")
                rtn_val = False

        else:
            self.result.set("ERROR: Could not read settings")
            rtn_val = False

        if self.progress_window:
            self.set_progress(100)
            self.close_progress()

        return rtn_val
        

    def SendButtonClicked(self):
        self.open_progress("Sending settings...")

        result = True

        # Update the LED OCD object
        if not self.update_uledocd():
            self.result.set("ERROR: Settings could not be updated")
            return False

        self.set_progress(5)

        self.led_ocd.SendSettings()
        self.set_progress(50)

        if result:
            if self.options["other"]["verify_sends"].get():
                self.set_progress_title("Verifying settings...")
                if self.verify_sent_settings(self.set_progress, 50, 90):
                    self.result.set("Settings sent and verified")
                    if self.options["backups"]["on_send"].get():
                        self.set_progress_title("Backing up...")
                        self.backup(tag="SENT")
                    rtn_val = True
                else:
                    self.result.set("ERROR: Settings were sent but did not verify! Try sending them again.")
                    rtn_val = False
            else:
                self.set_progress(90)
                self.result.set("Settings sent")
                if self.options["backups"]["on_send"].get():
                    self.set_progress_title("Backing up...")
                    self.backup(tag="SENT")
                rtn_val = True

        else:
            self.result.set("ERROR: Settings could not be sent or were only partially sent! Try sending them again.")
            rtn_val = False

        if self.progress_window:
            self.set_progress(100)
            self.close_progress()

        return rtn_val



    def verify_sent_settings(self, set_progress, progress, end):
        read_settings = self.led_ocd.SendReadSettingsCmd()[1]

        match self.manu_id.get():
            case Manufacturers.WPC | Manufacturers.CAPCOMA | Manufacturers.CAPCOMB:
                increment = (end-progress)/SETTINGS_OBJ_CNT_WPC
            case Manufacturers.STERN:
                increment = (end-progress)/SETTINGS_OBJ_CNT_STERN
            case _:
                return False
        
        increment = (end-progress)/SETTINGS_OBJ_CNT
        cnt = 0
        if read_settings:
            for x in read_settings:
                if isinstance(x, LampProfile):
                    if not self.settings["lamp_vars"][x.lamp_num-1].get() == x.profile_num:
                        return False
                    cnt += 1
                    progress += increment
                elif isinstance(x, ProfileName):
                    if not self.settings["profile_vars"][x.profile_num-1]["name"].get() == x.name:
                        return False
                    cnt += 1
                    progress += increment
                elif isinstance(x, ProfileDelay):
                    if not self.settings["profile_vars"][x.profile_num-1]["delay"].get() == x.delay:
                        return False
                    cnt += 1
                    progress += increment
                elif isinstance(x, ProfileBrightnessPercent):
                    if not self.settings["profile_vars"][x.profile_num-1]["brightnesses"][x.brightness_num-1].get() == x.percent:
                        return False
                    cnt += 1
                    progress += increment
            set_progress(progress)

            if cnt == SETTINGS_OBJ_CNT or cnt == SETTINGS_OBJ_CNT_STERN or cnt == SETTINGS_OBJ_CNT_WPC:
                return True
            else:
                return False 



    def SaveButtonClicked(self):
        if self.led_ocd.SendSaveSettingsCmd():
            self.result.set("Settings on the LED OCD board will be ratained after a power cycle")
            return True
        else:
            self.result.set("ERROR: Settings could not be saved to the LED OCD board")
            return False


    def ImportButtonClicked(self):
        load_from_filename = Querybox.get_open_filename(parent=self.app, initialdir=self.backups_dir, filetypes=[("XML files", "*.xml"), ("JSON files", "*.json"), ("All files", "*.*")])

        if load_from_filename:
            file_extension = os.path.splitext(load_from_filename)[1].lower()
            if file_extension == ".xml":
                result = self.load_from_xml_file(load_from_filename)
            elif file_extension == ".json":
                result = self.load_from_json_file(load_from_filename)
            else:
                # If another file type is selected assume it is XML
                result = self.load_from_xml_file(load_from_filename)

            if result:
                self.result.set(f"Settings successfully read from \"{load_from_filename}\"")
                return True
            else:
                self.result.set(f"ERROR: Could not read settings from \"{load_from_filename}\"")
                return False
        else:
            return False


    def ExportButtonClicked(self):
        if not self.update_uledocd():
            self.result.set("ERROR: Settings could not be updated")
            return False

        save_to_filename = Querybox.get_save_filename(parent=self.app, initialdir=self.backups_dir, defaultextension=".xml", filetypes=[("XML files", "*.xml"), ("JSON files", "*.json"), ("All files", "*.*")])
        file_extension = os.path.splitext(save_to_filename)[1].lower()

        if file_extension == ".xml":
            result = self.save_to_xml_file(save_to_filename)
        elif file_extension == ".json":
            result = self.save_to_json_file(save_to_filename)
        else:
            # If another file type is chosen default to XML
            result = self.save_to_xml_file(save_to_filename)

        if result:
            self.result.set(f"Settings exported to {save_to_filename}")
            return True
        else:
            self.result.set(f"ERROR: Settings could not be exported to {save_to_filename}")
            return False


    def ManualButtonClicked(self):
        if not self.manual_mode:
            self.saved_profile_7_brightnesses = [0, 0, 0, 0, 0, 0, 0, 0]
            read_settings = self.led_ocd.SendReadSettingsCmd()[1]

            cnt = 0
            if read_settings:
                for x in read_settings:
                    if isinstance(x, ProfileBrightnessPercent):
                        if x.profile_num == 7:
                            self.saved_profile_7_brightnesses[x.brightness_num-1] = x.percent
                            cnt += 1
            else:
                self.result.set("ERROR: Could not read settings! Manual mode canceled.")
                return False
            
            if cnt != 8:
                self.result.set("ERROR: Could not read settings - wrong number of values! Manual mode cancelled.")
                return False

            x = self.app.winfo_x() + self.app.winfo_width()//2 - self.manual_window_width//2
            y = self.app.winfo_y() + self.app.winfo_height()//2 - self.manual_window_height//2
            self.manual_window.geometry(f"+{x}+{y}")

            if self.led_ocd.SendManualCmd():
                self.manual_mode = True
                for x in self.gui_in_manual:
                    x.state(["!disabled"])
                for x in self.gui_in_manual_advanced:
                    if self.advanced:
                        x.state(["disabled"])
                    else:
                        x.state(["!disabled"])
                for x in self.gui_in_normal:
                    x.state(["disabled"])
                self.passthrough_button.state(["disabled"])
                self.manual_window.deiconify()
                self.result.set("Entered Manual Mode")
                return True
            else:
                self.manual_mode = False
                self.result.set("ERROR: Could not enter Manual Mode!")
                return False

        return True


    def ManualSendButtonClicked(self):
        if self.selected_manual_lamp.get() and self.selected_brightnesss_num.get() and len(self.manual_brightness_vars) == 8:
            for bnum in range(0,8):
                bright_val = self.manual_brightness_vars[bnum].get()
                if not self.led_ocd.SendSetPBCmd(pnum=7, brightnum=bnum+1, value=bright_val):
                    self.result.set("ERROR: Could not set bringthness values in Manual Mode")
                    return False

            if not self.led_ocd.SendSetLBCmd(lampnum = self.selected_manual_lamp.get(), bright = self.selected_brightnesss_num.get()):
                self.result.set("ERROR: Could not set lamp brightness number in Manual Mode")
                return False
        else:
            self.result.set("ERROR: One or more of the Manual Mode settings values are not set")
            return False

        self.result.set(f"Brightness #{self.selected_brightnesss_num.get()} set for lamp #{self.selected_manual_lamp.get()}")
        return True


    def ManualResetButtonClicked(self):
        if self.led_ocd.SendManualCmd():
            self.result.set("All lamps turned off")
            return True
        else:
            self.result.set("ERROR: could not turn lamps off")
            return False


    def KeepButtonClicked(self):
        spnum = self.selected_keep_profile_num.get()
        if spnum and len(self.manual_brightness_vars) == 8:
            if spnum != 7:
                for bnum in range(1,9):
                    if not self.led_ocd.SendSetPBCmd(pnum = 7, brightnum = bnum, value = self.saved_profile_7_brightnesses[bnum-1]):
                        self.result.set("ERROR: Could not restore profile 7 brightnesses! Try again and if it fails quit this tool and power cycle the pinball machine to restore the settings.")
                        return False

            for bnum in range(1,9):
                bval = self.manual_brightness_vars[bnum-1].get()
                self.settings["profile_vars"][spnum-1]["brightnesses"][bnum-1].set(bval)
                if not self.led_ocd.SendSetPBCmd(pnum = spnum, brightnum = bnum, value = bval):
                    self.result.set(f"ERROR: Could send profile #{spnum} brighness #{bnum} value {bval}! Try again and if it fails quit this tool and power cycle the pinball machine to restore the settings.")
                    return False

            self.manual_window.withdraw()
            self.result.set(f"Brightness values saved to profile #{self.selected_keep_profile_num.get()}")
            self.NormalButtonClicked()
            return True

        self.result.set("ERROR: No profile numbers selected or 8 brightness values aren't set (this shouldn't happen)")
        return False


    def PassthroughButtonClicked(self):
        if not self.manual_mode:
            if self.led_ocd.SendPassthroughCmd():
                self.manual_mode = True

                pwidth = 500
                pheight = 150
                self.passthru_window = Toplevel(master=self.app, title="Passthrough Mode", size=(pwidth, pheight), topmost=True)
                self.passthru_window.transient(master=self.app)
                self.passthru_window.resizable(False, False)
                self.passthru_window.on_close(self.passthrough_close)

                x = self.app.winfo_x() + self.app.winfo_width()//2 - pwidth//2
                y = self.app.winfo_y() + self.app.winfo_height()//2 - pheight//2
                self.passthru_window.geometry(f"+{x}+{y}")

                passthrough_window_frame_0 = Frame(self.passthru_window)
                passthrough_window_frame_0.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)

                passthrough_window_frame_1 = Frame(self.passthru_window)
                passthrough_window_frame_1.grid(sticky="nsew", column=0, row=1, padx=3, pady=(20,3))

                passthrough_window_frame_2 = Frame(self.passthru_window)
                passthrough_window_frame_2.grid(sticky="nsew", column=0, row=2, padx=(85,5), pady=((20,3)))

                instructions = Text(passthrough_window_frame_0, width=53, height=3, font = ("Arial", 12), wrap="word")
                instructions.insert("end", "Passthrough Mode temporarily disables the LED OCD board so you can see how it looks without it. When you are done click the Close button or close the window and it will return to LED OCD control.")
                instructions.configure(state="disabled")          
                instructions.grid(sticky="nsew", column=0, row=0, padx=3, pady=3)

                close_button = Button(passthrough_window_frame_1, text="Close", command=self.passthrough_close_button_clicked)
                ToolTip(close_button, text="Close and return control of the lamps to the LED OCD board")
                close_button.grid(sticky="nsew", column=0, row=0, padx=(200,40), pady=3)

                self.result.set("Entered Passthrough Mode - LED OCD is disabled until you close the Passthrough window")

                close_button.focus_set()
                self.passthru_window.grab_set()
                self.app.wait_window(self.passthru_window)
                self.passthru_window = None
                return True
            else:
                self.manual_mode = False
                self.result.set("ERROR: Could not enter Passthrough Mode!")
                return False


    def passthrough_close(self):
        self.NormalButtonClicked()
        return True


    def passthrough_close_button_clicked(self):
        self.NormalButtonClicked()
        self.passthru_window.destroy()


    def NormalButtonClicked(self):
        if self.manual_mode:
            if self.led_ocd.SendNormalOCDCmd():
                for x in self.gui_in_manual:
                    x.state(["disabled"])
                for x in self.gui_in_normal:
                    x.state(["!disabled"])
                if not self.advanced.get():
                    for x in self.gui_in_advanced:
                        x.configure(state="disabled", takefocus=False)
                    for x in self.gui_in_manual_advanced:
                        x.configure(state="disabled", takefocus=False)

                self.manual_mode = False

                self.result.set("Returned to Normal Mode")

                return True
            else:
                self.result.set("ERROR: Could not enter Normal Mode!")
                return False
        return True


def uledocd_gui():
    parser = argparse.ArgumentParser(description="GUI for the led_ocd and gi_ocd boards",
                                    usage="uledocd_gui [-h|--help] [-p|--port TTY] [-m|--manufacturer MANUFACTURER]",
                                    epilog="Example: uledocd_gui -p /dev/ttyUSB3 -m CAPCOMA")
    
    parser.add_argument("-p", "--port", dest="port_name", type=str, help="port name for LED OCD interface (if not provided it will detect serial ports)")
        
    parser.add_argument("-m", "--manufacturer", dest="manuf",
                        choices=["WPC", "STERN", "CAPCOMA", "CAPCOMB"],
                        type=str,
                        help="set the game manufacturer (if not provided it will attempt to detect the platform)")
    
    parser.add_argument("-d", "--data_dir", dest="data_dir",
                        type=str,
                        help=f"set the directory where game csv files are located (if not provided it will be \"{DEFAULT_DATA_DIR}\")")
    
    parser.add_argument("-g", "--game_file", dest="game_file",
                        type=str,
                        help="set the game (if not provided it will select a default based on manufacturer)")
    
    args = parser.parse_args()

    ULEDOCD_GUI(port_name = args.port_name if args.port_name else None, manufacturer= args.manuf if args.manuf else None, data_dir = args.data_dir if args.data_dir else None, game_file = args.game_file if args.game_file else None)

if __name__ == "__main__":
    uledocd_gui()
