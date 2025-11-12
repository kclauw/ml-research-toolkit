import autoroot
from wandb_tools import download_runs
import utils
import os

def get_output_folder(cfg, base_folder):
    env_name = cfg["env_id"]
    env_params = utils.select_keys_from_dict(cfg, ["num_envs", "num_steps"])
    agent_params = utils.select_keys_from_dict(cfg, ["num_envs", "num_steps"])
    
    return os.path.join(base_folder, env_name)

download_runs("kclauw", "cleanRL", get_output_folder, "./results")