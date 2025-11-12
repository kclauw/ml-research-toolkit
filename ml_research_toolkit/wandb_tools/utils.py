import wandb
import pandas as pd 
import os

def filter_run(cfg1, cfg2):
    match = True
    for k in cfg1:
        if cfg1.get(k) != cfg2[k]:
            return False
    return match

def download_runs(entity, project, get_output_folder, base_folder):
    api = wandb.Api()
    runs = api.runs(entity + "/" + project)
        
    
    for run in runs:
        config = {k: v for k, v in run.config.items() if not k.startswith("_")}
        for k, v in config.items():
            print((k, v))
        
        output_folder = get_output_folder(config, "./results")
        print(output_folder)
   
        
     