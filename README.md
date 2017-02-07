# Task laptop upgrade instructions

1. Upgrade the operating system.
2. Download [Miniconda](https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh)
3. Do the following:

    * Install miniconda: `bash Miniconda3-latest-MacOSX-x86_64.sh`
    * Fix path issues: `python setup.py`
    * Restart terminal so python version will take effect
    * Install: `sudo python setup.py`
    * Get pyzmq: `conda install pyzmq`
    * Allow through firewall
      `cd ~/RAM_3.0; ./run_experiment --no-fs --experiment=FR1 --subject=test`
      then agree to the popup
