# Task laptop upgrade instructions

1. Upgrade the operating system.
2. Download [Miniconda](https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh)
3. Clone or download this repository
4. Do the following:

    * Install miniconda: `bash Miniconda2-latest-MacOSX-x86_64.sh`
    * Fix path issues: `python setup.py`
    * Restart terminal so python version will take effect
    * Install: `python setup.py`
    * Get pyzmq: `conda install pyzmq`
    * `cd ~/RAM_3.0`
    * `git submodule init`
    * `git submodule update`
    * Plug in an ethernet cable to connect the task laptop to the host PC
    * Extract videos: `./vidextract.sh`
    * Allow through firewall:
      `cd ~/RAM_3.0; ./run_experiment --no-fs --experiment=FR1 --subject=test`
      then agree to the popup
