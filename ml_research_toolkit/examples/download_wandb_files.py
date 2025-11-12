import autoroot
from wandb_tools import download_runs
import os

def get_output_folder(cfg, base_folder):
    env_name = cfg["env_id"]
    
    return os.path.join(base_folder, env_name)

download_runs("kclauw", "cleanRL", get_output_folder, "./results")