# PyEPL: hardware/sound/setup.py
#
# Copyright (C) 2003-2005 Michael J. Kahana
# Authors: Ian Schleifer, Per Sederberg, Aaron Geller, Josh Jacobs
# URL: http://memory.psych.upenn.edu/programming/pyepl
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See the license.txt that came with this file.

from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

import sys


# #+++HACK: replace linker gcc with g++ +++++++++++
# gpp_exe = 'g++'
# gcc_exe = 'g++'
# from distutils import sysconfig
# save_init_posix = sysconfig._init_posix
# def my_init_posix():
#     save_init_posix()
#     g = sysconfig._config_vars
#     for n,r in [('LDSHARED',gpp_exe),('CC',gcc_exe)]:
#         if g[n][:3]=='gcc':
#             print 'my_init_posix: changing %s = %r'%(n,g[n]),
#             g[n] = r+g[n][3:]
#             print 'to',`g[n]`
# sysconfig._init_posix = my_init_posix
# #++++++++++++++++++++++++++++++++++++++++++++++++



sndSources = ["sound.pyx","eplsound_wrapper.cpp","eplSound.cpp","RtAudio.cpp"]

if sys.platform == "darwin":
    defines = [('__MACOSX_CORE__', None)]
    libs = ["pthread"]
    x_link_args = ["-framework CoreAudio"] 
elif sys.platform.find('linux') != -1:
    defines = [('__LINUX_OSS__', None)]
    libs = ["pthread"]
    x_link_args = []

ext_sound = [Extension("sound",
                       sndSources,
                       libraries = libs,
                       define_macros=defines,
                       extra_link_args=x_link_args)
             ]

setup(
  name = "sound",
  ext_modules=ext_sound,
  cmdclass = {'build_ext': build_ext}
)
