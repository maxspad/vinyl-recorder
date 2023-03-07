import psutil
import shutil

def get_res_stats():
    hdd = shutil.disk_usage('.')
    return {
        'mem': int(psutil.virtual_memory().percent),
        'cpu': int(psutil.cpu_percent()),
        'hdd': int(float(hdd.used) / hdd.free * 100)
    }
