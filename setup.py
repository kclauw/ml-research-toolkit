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
        "wandb",
    ],
    python_requires=">=3.8",
    description="Toolkit for RL/ML experiments: utils, visualizer, cluster runner, monitor, wandb helper",
    author="Kenzo Clauw",
    #author_email="your_email@example.com",
    url="https://github.com/kclauw/ml-research-toolkit",
)
