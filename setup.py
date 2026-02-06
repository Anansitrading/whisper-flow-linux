from setuptools import setup, find_packages

setup(
    name="whisperflow",
    version="1.0.0",
    description="Local push-to-talk speech-to-text for Linux",
    author="Anansitrading",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "faster-whisper>=1.0.0",
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
        "pynput>=1.7.6",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "whisperflow=whisperflow.__main__:main",
        ],
    },
)
