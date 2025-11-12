from setuptools import setup, find_packages

setup(
    name="ml_research_toolkit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "matplotlib",
        "pandas",
        "pyyaml",
        "wandb",   # optional
    ],
    python_requires=">=3.9",
    description="Toolkit for RL/ML experiments: utils, visualizer, cluster runner, monitor, wandb helper",
    author="Your Name",
    url="https://github.com/kclauw/ml_research_toolkit",
)