# Task laptop upgrade instructions

## WARNING

These instructions are for upgrading PyEPL to work with System 3.0 based on an
already existing System 2 setup. The following steps should not be followed
for upgrading from version 3.0 to version 3.1. Instead, see the
[RAMControl][] repository.

## Instructions

The following steps must be performed by the `exp`. You must also first
**temporarily grant admin rights** to the `exp` user.

**IMPORTANT**: Remember to remove admin rights once everything is confirmed to
be working!

1. Upgrade the operating system to Sierra (this can be done through the App
   Store).
2. Download [Miniconda](https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh)
3. Upgrade PyEPL (crossed out stuff is old and probably only applies to version 3.0):

    * Install miniconda and accept all defaults: `bash Miniconda2-latest-MacOSX-x86_64.sh`
    * Clone or download this repository: `git clone https://github.com/ramdarpaprojectorg/pyepl_upgrade.git`
    * Fix path issues: `python setup.py`
    * Restart terminal so python version will take effect
    * Install: `sudo python setup.py`
    * Get pyzmq: `conda -y install pyzmq`
    * Clone RAMControl 3.1 and follow all instructions there (see [RAMControl][])
    * ~~Fix permissions: `sudo chown -R exp ~/RAM_3.0`~~
    * ~~`cd ~/RAM_3.0`~~
    * ~~`git submodule init`~~
    * ~~`git submodule update`~~
    * ~~Extract videos: `./vidextract.sh`~~
    * For upload, copy the RAMTransfer-keys from previous installation: `cp ~/RAM_2.0/source/RAMTransfer-Keys ~/RAM_3.1/source/`
    * Set permissions on the keys: `chmod 600 ~/RAM_3.1/source/RAMTransfer-keys/*`
    * So the password for the key is saved in the laptop keychain, create a file ~/.ssh/config that reads:
            Host *
                  UseKeychain yes
    * Run upload tool and type in keychain password when prompted.
    * Connect the task laptop to the host PC via ethernet cable
    * Allow through firewall:
      `cd ~/RAM_3.1; ./run_experiment -d --experiment=FR1 --subject=R0000X`
      then agree to the popup.

5. Fix System 1 and System 2 run scripts to be able to continue using them:
    * Edit run scripts (using XCode) and change the line `PYTHON_CMD="python2.6"` to `PYTHON_CMD="python"`.
    * Run by double clicking the run script as usual.

[RAMControl]: https://github.com/ramdarpaprojectorg/RAMControl
