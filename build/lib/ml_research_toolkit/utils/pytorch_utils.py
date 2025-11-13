import utils 
import random
import torch
import numpy as np 
import os 

def save_checkpoint(
    agent,
    optimizer,
    args,
    global_step,
    folder="./checkpoints",
    best=False,
    tag=None,
    overwrite=False,
):
    """
    Save a model checkpoint with RNG states, config, and optional overwrite.

    Args:
        agent: Model or agent with state_dict().
        optimizer: Optimizer with state_dict().
        args: Training arguments (e.g., from argparse).
        global_step (int): Training step or episode number.
        folder (str): Directory where checkpoints are saved.
        best (bool): Whether this is the best-performing checkpoint.
        tag (str, optional): Optional string tag for filename.
        overwrite (bool): If True, overwrite the same checkpoint file each time.
    """
    utils.create_folder(folder)

    if overwrite:
        filename = "latest_checkpoint.pt"
    else:
        filename = f"checkpoint_step_{global_step}"
        if tag:
            filename += f"_{tag}"

    path = os.path.join(folder, filename)

    # Save full training state
    state = {
        "global_step": global_step,
        "agent_state_dict": agent.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "args": vars(args),
        "random_state": random.getstate(),
        "numpy_rng": np.random.get_state(),
        "torch_rng": torch.get_rng_state(),
        "torch_cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }

    torch.save(state, path)

    if best:
        best_path = os.path.join(folder, "best_checkpoint.pt")
        torch.save(state, best_path)

    print(f"[Checkpoint] Saved at step {global_step}: {path}")
    if best:
        print(f"[Checkpoint] Updated best model at: {best_path}")

    return path

def load_checkpoint(path, agent, optimizer=None, device=torch.device("cpu")):
    """
    Load a checkpoint, restoring agent, optimizer, and RNG states.

    Args:
        path (str): Path to checkpoint file.
        agent: Model or agent with load_state_dict().
        optimizer (optional): Optimizer to restore state_dict.
        device (torch.device): Device to load model/optimizer to.

    Returns:
        global_step (int): Step at which checkpoint was saved.
    """
    assert os.path.isfile(path), f"Checkpoint not found: {path}"
    
    # fix for PyTorch 2.6+ unpickling
    ckpt = torch.load(path, map_location=device, weights_only=False)

    # load agent
    agent.load_state_dict(ckpt["agent_state_dict"])

    # load optimizer if provided
    if optimizer is not None and ckpt.get("optimizer_state_dict") is not None:
        try:
            optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        except Exception:
            # handle device mismatch for optimizer tensors
            for state in ckpt["optimizer_state_dict"].get("state", {}).values():
                for k, v in list(state.items()):
                    if isinstance(v, torch.Tensor):
                        state[k] = v.to(device)
            optimizer.load_state_dict(ckpt["optimizer_state_dict"])

    # restore RNGs if present
    if "random_state" in ckpt:
        random.setstate(ckpt["random_state"])
    if "numpy_rng" in ckpt:
        np.random.set_state(ckpt["numpy_rng"])
    if "torch_rng" in ckpt:
        torch.set_rng_state(ckpt["torch_rng"])
    if "torch_cuda_rng" in ckpt and torch.cuda.is_available():
        try:
            torch.cuda.set_rng_state_all(ckpt["torch_cuda_rng"])
        except Exception:
            pass

    global_step = ckpt.get("global_step", 0)
    print(f"[Checkpoint] Loaded checkpoint from step {global_step}: {path}")
    return global_step