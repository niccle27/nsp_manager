#!/usr/bin/python3
import time
import subprocess
from typing import List
import yaml
from pathlib import Path
from dataclasses import dataclass
import argparse


# Dataclasses
@dataclass
class RunningAppData:
    window_id: str
    pid: int
    class_name: str
    title: str
    # def __init__(self, window_id, pid, class_name):
    #     self.window_id = window_id
    #     self.pid = pid
    #     self.class_name = class_name

@dataclass
class AppLaunchConfig:
    class_name: str
    launch_cmd: str
    title_matching: str = None
    

# Utils
def read_yaml(path):
    with open(path, "r") as reader:
        data = yaml.load(reader, yaml.SafeLoader)
        return data

def write_yaml(data, path):
    with open(path, "w") as writer:
        yaml.dump(data, writer)

# Constants
HOME = Path.home()
PATH_DATA_CONFIG = HOME / Path(".config/nsp_manager/config.yaml")
PATH_DATA_CONFIG.parent.mkdir(exist_ok=True, parents=True)
PATH_DATA_CONFIG.touch(exist_ok=True)
PATH_DATA_SESSION = Path("/tmp/nsp_temp_session.yaml")
PATH_DATA_SESSION.touch(exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--key", type=str, help="help", default="firefox")
args = parser.parse_args()

KEY = args.key
NSP_WS = "10"

# Check information
CURRENT_WS = subprocess.check_output(['xdotool', 'get_desktop']).decode().strip()
current_session = read_yaml(PATH_DATA_SESSION)  or {}
config_apps = read_yaml(PATH_DATA_CONFIG)  or {}

# Check if app key is in config
config_app = config_apps.get(KEY)
app_launch_config = None
if config_app is None:
    exit(0)
else:
    app_launch_config = AppLaunchConfig(**config_app)

# Parsing list of windows id, pid classname and title
wmctrl_output = subprocess.check_output(['wmctrl', '-lpx']).decode().split('\n')
list_running_app: List[RunningAppData] = []
for line in wmctrl_output:
    if len(line)==0:
        continue
    line = [e for e in line.split(" ") if len(e)>0]
    window_id, _, pid, class_name, *title = line
    list_running_app.append(RunningAppData(window_id, pid, class_name, title=" ".join(title)))

list_window_id_before = [e.window_id for e in list_running_app]
not_done = True
app = None

# if no current session for key if current session do not match config
if KEY not in current_session:
    pass
# if current session do not correspond to a window id in the list
elif current_session[KEY]["window_id"] not in list_window_id_before: 
    # if title matching option is available
    if ((app_launch_config.title_matching is not None and app_launch_config.title_matching != "")):
        # over the current running app list, is there one that match
        for running_app in list_running_app:
            if (running_app.class_name == app_launch_config.class_name and \
                app_launch_config.title_matching in running_app.title):
                app = running_app
                current_session = {**current_session, **{KEY: app.__dict__}}
                break

else:
    app = RunningAppData(**current_session[KEY])

# if app is not None:
#     # index_running_app = list_window_id_before.index(current_session[KEY]["window_id"])
#     # running_app = list_running_app[index_running_app]
#     if (running_app.class_name==app_launch_config.class_name ):
#         if app_launch_config.title_matching is not None:
#             if app_launch_config.title_matching not in running_app.title:
#                 app = None


# if app could be found move to current or hide from current and focus
if app is not None:
    # if (app.class_name == app_launch_config.class_name and 
    #     app.window_id in list_window_id_before):
    current_ws_id = subprocess.check_output(['xdotool', 'get_desktop_for_window', app.window_id]).decode().strip()
    if current_ws_id == "10":
        subprocess.check_output(['xdotool', 'set_desktop_for_window', app.window_id, str(CURRENT_WS)])
    else:
        print("move to ")
        subprocess.check_output(['xdotool', 'set_desktop_for_window', app.window_id, str(NSP_WS)])
        try:
            subprocess.check_output(['xdotool', 'windowfocus', "--sync", app.window_id])
        except Exception as e:
            pass
# else launch the app and add save windows data
else:
    process = subprocess.Popen(app_launch_config.launch_cmd.split(" "))
    time.sleep(3)
    wmctrl_output = subprocess.check_output(['wmctrl', '-lpx']).decode().split('\n')
    list_running_app: List[RunningAppData] = []
    for line in wmctrl_output:
        if len(line)==0:
            continue
        # print(line)
        line = [e for e in line.split(" ") if len(e)>0]
        window_id, _, pid, class_name, *title = line
        list_running_app.append(RunningAppData(window_id, pid, class_name, " ".join(title)))
        
    for window in list_running_app:
        if (window.window_id not in list_window_id_before and \
            window.class_name == app_launch_config.class_name):
            if app_launch_config.title_matching is not None:
                if app_launch_config.title_matching not in window.title:
                    continue
            try:
                subprocess.check_output(['xdotool', 'windowfocus', "--sync", window.window_id])
            except Exception as e:
                pass
            current_session = {**current_session, **{KEY: window.__dict__}}
write_yaml(current_session, PATH_DATA_SESSION)
 
