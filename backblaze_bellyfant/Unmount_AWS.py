import os
import shutil
import apsync as aps

def kill_rclone():
    os.system("taskkill /im rclone.exe")

    clear_cache()

def clear_cache():
    settings = aps.Settings()    
    cache_path = settings.get("cachepath",default=get_default_cache_path())

    vfs_path = os.path.join(cache_path,"vfs")
    vfs_metaPath = os.path.join(cache_path,"vfsMeta")

    if os.path.isdir(vfs_path):
        shutil.rmtree(vfs_path)

    if os.path.isdir(vfs_metaPath):
        shutil.rmtree(vfs_metaPath)

def get_default_cache_path():
    app_data_roaming = os.getenv('APPDATA')
    app_data = os.path.abspath(os.path.join(app_data_roaming, os.pardir))
    return os.path.join(app_data,"Local/rclone").replace("/","\\")

kill_rclone()

#print(shutil.which("WinFsp"))