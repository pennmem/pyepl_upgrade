from distutils.sysconfig import get_python_lib
import shutil
import os
import sys
import re
import subprocess
    
HOME = os.environ['HOME']
SITE_PKG_REPLACE = '__SITE_PACKAGE_DIR__'
INSTALL_FILE = './installed_files.txt'
LN_FILES = {'/opt/local/lib/libFLAC.8.2.0.dylib' : '/opt/local/lib/libFLAC.8.dylib',
            '/usr/local/lib/liblabjackusb-2.0.3.dylib' : '/usr/local/lib/liblabjackusb.dylib'}

RAM_CONTROL_GIT = 'https://github.com/ramdarpaprojectorg/RAMControl.git'
RAM_CONTROL_LOCATION = os.path.join(HOME, 'RAM_3.0')

UNTARS = 'experiments/RAM_FR/videos.tar.xz', 'experiments/RAM_catFR/videos.tar.xz'

USER = subprocess.check_output(['who', 'am', 'i']).split()[0]

def confirm(message):
    rsp = raw_input(message)
    while rsp.lower() not in ('y', 'n'):
        print 'Please enter "y" or "n"'
        rsp = raw_input(message)
    return rsp == 'y'

def fix_bash_init(filename):
    if not os.path.exists(filename):
        print '%s does not exist. Skipping' % (filename)
    changed = False
    with open(filename, 'r') as file:
        lines = []
        for line in file:
            if 'alias python' not in line:
                lines.append(line)
            else:
                if not confirm("The line \"%s\" exists in %s. OK to remove? " % (line.strip(), filename)):
                    lines.append(line)
                else:
                    changed = True
    
    if changed:
        print 'Writing over %s' % (filename)
        with open(filename, 'w') as out_file:
            out_file.write(''.join(lines))
    else:
        print 'No changes to make to %s' % (filename) 
    return changed

def copy_files():
    site_packages = get_python_lib()

    files = [x.strip() for x in open(INSTALL_FILE).readlines()]

    for file in files:
        if file[-3:] == 'pyc':
            continue
        source = './'+file
        destination = file.replace(SITE_PKG_REPLACE, site_packages)
        dest_dir, _ = os.path.split(destination)

        if os.path.exists(destination):
            print('Overwriting %s' % destination)
            #if not confirm("%s already exists. Do you want to overwrite? " % destination):
            #    continue
        try:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                print("Created %s" % (dest_dir))
            shutil.copyfile(source, destination)
            print("Copied %s to %s" % (source, destination))
        except:
            print("WARNING: Could not copy %s to %s" % (source, destination))

def link_files():
    for source, dest in LN_FILES.items():
        os.system("ln -s %s %s" % (source, dest))
        print("Linked %s to %s" % (source, dest))

def check_for_conda():

    site_packages = get_python_lib()

    if not ('anaconda' in site_packages or 'miniconda' in site_packages):
        if not confirm("It appears you are not installing into a conda environment.\n" \
                       "Site packages is %s\n" % site_packages + "" 
                       "Are you sure you want to continue? "):
            exit(0)
    else:
        if not confirm("Installing into python site-packages located at %s. Do you want to continue? " % (site_packages)):
            exit(0)

def clone_ram_control():
    clone_cmd = ['git', 'clone', RAM_CONTROL_GIT, RAM_CONTROL_LOCATION]
    
    submodule_commands = [
        ['git', 'submodule', 'init'],
        ['git', 'submodule', 'update']
    ]

    untar_command = [ 'tar', '-xvf']
    
    chown_command = ['chown', '-R', USER, RAM_CONTROL_LOCATION]
    
    cwd = os.getcwd()
    subprocess.call(clone_cmd)
    os.chdir(RAM_CONTROL_LOCATION)
    for cmd in submodule_commands:
        subprocess.call(cmd)
    
    for tar in UNTARS:
        print("Extracting %s"%tar)
        subprocess.call(untar_command + [tar])

    os.chdir(cwd)
    
    subprocess.call(chown_command)

def sign_python():
    executable = sys.executable
    cmd = ['codesign', '-f', '--verbose', '--deep', '-s', 'UPenn-RAM', executable]
    verify_cmd = ['codesign', '-dvvvv', executable]
    print 'Signing ', executable
    subprocess.call(cmd)
    subprocess.call(verify_cmd)


def run():
    changed_rc = fix_bash_init(os.path.join(HOME, '.bashrc'))
    changed_profile = fix_bash_init(os.path.join(HOME, '.bash_profile'))

    if changed_rc or changed_profile:
        print("Due to a change in bash initialization, it is recommended that you restart your terminal before continuing")
        exit(0)
    
    check_for_conda()
    copy_files()
    link_files()

    print("Attempting to disable network time...")
    os.system("systemsetup -setusingnetworktime off")
    
    print("Cloning RAM repositories")
    clone_ram_control()
    
    sign_python()
    print("Installation complete")

if __name__ == '__main__':
    run()
