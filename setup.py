#!/usr/bin/env python

###########################################################
##                                                       ##
##   setup.py                                            ##
##                                                       ##
##                Author: Tony Fischetti                 ##
##                        tony.fischetti@gmail.com       ##
##                                                       ##
###########################################################
#
##############################################################################
#                                                                            #
# Copyright (c) 2013, 2014, Tony Fischetti                                   #
#                                                                            #
# MIT License, http://www.opensource.org/licenses/mit-license.php            #
#                                                                            #
# Permission is hereby granted, free of charge, to any person obtaining a    #
# copy of this software and associated documentation files (the "Software"), #
# to deal in the Software without restriction, including without limitation  #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,   #
# and/or sell copies of the Software, and to permit persons to whom the      #
# Software is furnished to do so, subject to the following conditions:       #
#                                                                            #
# The above copyright notice and this permission notice shall be included in #
# all copies or substantial portions of the Software.                        #
#                                                                            #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,   #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL    #
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING    #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER        #
# DEALINGS IN THE SOFTWARE.                                                  #
#                                                                            #
##############################################################################

from distutils.core import setup
from sakelib import constants


setup(name=constants.NAME,
      version=constants.VERSION,
      description=constants.DESCRIPTION,
      author=constants.AUTHOR_NAME,
      author_email=constants.AUTHOR_EMAIL,
      url=constants.URL,
      license='MIT',
      long_description="""
      Sake is a way to easily design, share, build, and visualize workflows
      with intricate interdependencies. Sake is self-documenting because the
      instructions for building a project also serve as the documentation of
      the project's workflow. The first time it's run, sake will build all
      of the components of a project in an order that automatically satisfies
      all dependencies. For all subsequent runs, sake will only rebuild the
      parts of the project that depend on changed files. This cuts down on
      unnecessary re-building and lets the user concentrate on their work
      rather than memorizing the order in which commands have to be run.

      For more information and documentation, check out this project's
      website: http://tonyfischetti.github.io/sake/
      """,
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Operating System :: OS Independent',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Utilities',
                   'Topic :: Software Development',
                   'Topic :: Documentation',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2'],
      packages=['sakelib'],
      requires=['networkx (>=1.8)',
                'PyYAML (>=3.0)'],
      scripts=['sake']
     )

if __name__ == '__main__':
    print("I hope you enjoy using Sake!")
