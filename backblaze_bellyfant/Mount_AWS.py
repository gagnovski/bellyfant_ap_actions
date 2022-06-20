from ast import arguments
from re import sub
import anchorpoint as ap
import apsync as aps
import platform
import subprocess
import os
import urllib.request

ctx = ap.Context.instance()
ui = ap.UI()

drive_var = "drive"
cache_var = ""
bucket_name = ctx.inputs["bucket_name"]
remote_dir = ctx.inputs["bucket_folder"]
server_name = ctx.inputs["server_name"]
rclone_path = os.path.join(ctx.yaml_dir,"rclone.exe")
rclone_config = os.path.join(ctx.yaml_dir,"rclone.conf")

def get_unused_drives():
    import string
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if not bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives

def create_bat_file(command,drive):    
    app_data = os.getenv('APPDATA')
    startup_path = f'{app_data}/Microsoft/Windows/Start Menu/Programs/Startup/ap_mount_{drive}.bat'
    with open(startup_path,'w') as f:
        f.write(command)

def setup_mount(dialog):
    drive = dialog.get_value(drive_var)
    cache_path = dialog.get_value(cache_var)

    if not os.path.isdir(cache_path):
        os.mkdir(cache_path)

    settings = aps.Settings()
    settings.set("cachepath", cache_path)
    settings.store()

    arguments = [
        rclone_path,                
        f"--config={rclone_config}",
        "mount",
        f"{server_name}:{bucket_name}/{remote_dir}",
        f"{drive}:",
        "--vfs-cache-mode",
        "full",
        "--network-mode",
        "-L",
        "--copy-links",
        "--use-server-modtime",
        "--poll-interval",
        "10s",
        "--cache-dir",
        cache_path,
        "--volname=Bellyfant"
    ]


    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE


    subprocess.Popen(
        arguments, startupinfo = startupinfo, shell=False
    )

    ui.show_success("Mount Successful")
    #create_bat_file("process "+f'{drive}: "'+f'{ctx.path}"',drive)
    dialog.close()

def get_default_cache_path():
    app_data_roaming = os.getenv('APPDATA')
    app_data = os.path.abspath(os.path.join(app_data_roaming, os.pardir))
    return os.path.join(app_data,"Local/rclone").replace("/","\\")

# def download_winfsp():

#     winget = subprocess.run(
#         "winget install -e --id WinFsp.WinFsp --accept-source-agreements", capture_output=True
#     )
#     if winget.returncode != 0:
#         print(winget.stderr)
#         ui.show_error("Failed to install WinFsp", description="Google WinFsp and install it manually.")
#     else:
#         ui.show_success("WinFsp Installed")
#         show_options()


def show_options():    
    drives = get_unused_drives()

    if len(drives) == 0:
        ui.show_error("No drives to mount", "Unmount another drive first")
        return

    dialog = ap.Dialog()
    dialog.title = "Mount Bellyfant Cloud Drive"

    if ctx.icon:
        dialog.icon = ctx.icon

    settings = aps.Settings()    
    cache_path = settings.get("cachepath",default=get_default_cache_path())

    dialog.add_text("Drive Letter:\t").add_dropdown(drives[0], drives, var=drive_var)
    dialog.add_text("Cache Location:\t").add_input(cache_path, browse=ap.BrowseType.Folder, var=cache_var)
    dialog.add_button("Mount", callback=setup_mount)

    dialog.show()

if platform.system() == "Darwin":
    ui.show_error("Unsupported Action", "This action is only supported on Windows :-(")
else:

    winfsp_path = os.path.join(os.environ["ProgramFiles(x86)"],"WinFsp/bin/launcher-x64.exe")
    if os.path.isfile(winfsp_path):
        show_options()
    else:
        ui.show_info("Need to install WinFSP first", description="This is required to stream files from AWS")
        #ctx.run_async(download_winfsp)

