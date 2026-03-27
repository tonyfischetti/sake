#!/usr/bin/env python

# this is a mess of duplicated code, I'll clean it up later


#####################################
##                                 ##
##  FUNCTIONALLY TESTS ENTIRE API  ##
##                                 ##
#####################################

from __future__ import unicode_literals
from __future__ import print_function
from difflib import ndiff
import hashlib
import io
import locale
import os
import platform
import shutil
from subprocess import Popen, PIPE
import sys
import time

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)

## !!!!!!!!!!! change directory later

# Determine sake command based on platform
if platform.system() == 'Windows':
    SAKE_CMD = 'python ../../sake'
else:
    SAKE_CMD = '../../sake'

# File lists used by ASSERT_FILES
FULL_BUILD_FILES = [
    "./graphfuncs.o", "./infuncs.o", "./VERSION.txt", "./qstats.o", "./statfuncs.o",
    ".shastore", "qstats", "qstats-documentation.html", "qstats.tar.gz"
]
WILDCARD_BUILD_FILES = [
    "./graphfuncs.o", "./infuncs.o", "./qstats.o", "./statfuncs.o",
    ".shastore", "qstats"
]


def get_sha(a_file):
    """
    Returns sha1 hash of the file supplied as an argument
    """
    try:
        BLOCKSIZE = 65536
        hasher = hashlib.sha1()
        with io.open(a_file, "rb") as fh:
            buf = fh.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fh.read(BLOCKSIZE)
        the_hash = hasher.hexdigest()
    except IOError:
        errmes = "File '{}' could not be read! Exiting!\n".format(a_file)
        sys.stdout.write(errmes)
        sys.exit(1)
    except:
        errmes = "Unspecified error returning sha1 hash. Exiting!\n"
        sys.stdout.write(errmes)
        sys.exit(1)
    return the_hash

def FAIL(message):
    sys.stderr.write("\033[91m" + message + "\n")
    sys.exit(1)

def run(command, spit_output=False):
    encoding = locale.getpreferredencoding()
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    # if p.returncode:
    #     print("Command '{}' failed!".format(command))
    #     print(err)
    #     sys.exit(1)
    if spit_output:
        print("\nTHIS WAS THE OUTPUT:\n{}\n=======".format(out.decode(encoding)))
        print("\nTHIS WAS THE ERR:\n{}\n=======".format(err.decode(encoding)))
    # Normalize line endings for cross-platform compatibility
    out_str = out.decode(encoding).replace('\r\n', '\n')
    err_str = err.decode(encoding).replace('\r\n', '\n')
    return out_str, err_str

def passed(whichtest):
    print("{:>45} {:>15}".format(whichtest, "\033[92mpassed\033[0m"))

def ASSERT(testmessage, observed, expected):
    if observed != expected:
        sys.stderr.write("\033[91m[FAILED]  " + testmessage + "\n")
        sys.stderr.write("OBSERVED: " + str(observed) + "\n")
        sys.stderr.write("EXPECTED: " + str(expected) + "\n")
        sys.exit(1)
    else:
        sys.stderr.write("\033[92m[PASSED]  " + testmessage + "\033[0m\n")

def ASSERT_FILES(testmessage, expected, files=None):
    if files is None:
        files = FULL_BUILD_FILES
    observed = ' '.join(f + '=' + str(os.path.isfile(f)) for f in files)
    exp_str = ' '.join(f + '=' + str(expected) for f in files)
    ASSERT(testmessage + " / file check", observed, exp_str)

##################
#  start clean  ##
##################
# let's start off clean
out, err = run(SAKE_CMD + "  clean")
# not relying on it being clean or not
### check for any file
ASSERT_FILES("start clean", False)


######################
#  sake recon full  ##
######################
# let's make sure it says it should build all targets
## RECON STILL MAKES .shastore!
out, err = run(SAKE_CMD + " -r")
expected = """Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
Would run target: build binary
Would run target: generate html documentation
Would run target: ensure version match
Would run target: output version text file
Would run target: package it
"""
ASSERT("sake recon full", out, expected)
ASSERT_FILES("sake recon full", False)


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run(SAKE_CMD + " ")
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -w -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Running target generate html documentation
pandoc -f markdown -t html qstats.md -o qstats-documentation.html
Running target ensure version match
./ensure_version_match.sh
Running target output version text file
bash -c "cat <(echo -n 'qstats version ') <(cat qstats-documentation.html | grep version | perl -pe 's/.*version (.+?)\)<.*/\\1/') | figlet > VERSION.txt"
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
ASSERT("sake build full", out, expected)
ASSERT_FILES("sake build full", True)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake build full / qstats output", out, "3\n")


#####################
#  sake recon full  #
#####################
# confirm it says nothing should be built
out, err = run(SAKE_CMD + "  -r")
ASSERT("sake recon full (no rebuild)", out, "")


######################
#  sake build full  ##
######################
# confirm nothing happens
out, err = run(SAKE_CMD + " ")
ASSERT("sake build full (no rebuild)", out, "Done\n")


###########################
#  sake recon clean full  #
###########################
# confirm would remove everything but doesn't
out, err = run(SAKE_CMD + "  -r clean")
expected = """Would remove file: .shastore
Would remove file: VERSION.txt
Would remove file: graphfuncs.o
Would remove file: infuncs.o
Would remove file: qstats
Would remove file: qstats-documentation.html
Would remove file: qstats.o
Would remove file: qstats.tar.gz
Would remove file: statfuncs.o
"""
ASSERT("sake recon clean full", out, expected)
ASSERT_FILES("sake recon clean full", True)



#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


##############################
## sake recon parallel full  #
##############################
# confirm would run everything and compile all
# objects in parallel
out, err = run(SAKE_CMD + "  -r -p")
expected = """Would run targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Would run targets 'build binary, generate html documentation' in parallel
Would run targets 'ensure version match, output version text file, package it' in parallel
"""
ASSERT("sake recon parallel full", out, expected)
ASSERT_FILES("sake recon parallel full", False)


########################
## sake parallel full  #
########################
# confirm builds all and builds correctly
out, err = run(SAKE_CMD + "  -p")
expected = """Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Going to run these targets 'build binary, generate html documentation' in parallel
Going to run these targets 'ensure version match, output version text file, package it' in parallel
Done
"""
ASSERT("sake parallel full", out, expected)
ASSERT_FILES("sake parallel full", True)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake parallel full / qstats output", out, "3\n")


##########################
#  sake "build twinary"  #
##########################
# confirm that it errors and says there is no such target
out, err = run(SAKE_CMD + '  "build twinary"')
ASSERT('sake "build twinary"', err, "Error: Couldn't find target 'build twinary' in Sakefile\n")


#########################
#  sake "build binary"  #
#########################
# confirm that it doesn't build
out, err = run(SAKE_CMD + '  "build binary"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Done
"""
ASSERT('sake "build binary"', out, expected)


###############################
#  sake force "build binary"  #
###############################
# confirm that it forces a build of binary
out, err = run(SAKE_CMD + '  -F "build binary"')
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Done
"""
ASSERT('sake force "build binary"', out, expected)


##################################
#  sake recon "compile objects"  #
##################################
# won't do anything
##### 
##### BUT DO MORE THINGS NEED TO BE ADDED TO "DONT UPDATE"?
##### 
##### 
out, err = run(SAKE_CMD + '  clean')
out, err = run(SAKE_CMD + ' ')
out, err = run(SAKE_CMD + '  -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
"""
ASSERT('sake recon "compile objects"', out, expected)


########################################
#  sake force recon "compile objects"  #
########################################
out, err = run(SAKE_CMD + '  -F -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
Would run target: ensure version match
"""
ASSERT('sake force recon "compile objects"', out, expected)


##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects
out, err = run(SAKE_CMD + '  -F "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -w -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target ensure version match
./ensure_version_match.sh
Done
"""
ASSERT('sake force "compile objects"', out, expected)


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


########################################
#  sake force recon "compile objects"  #
########################################
out, err = run(SAKE_CMD + '  -F -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
Would run target: ensure version match
"""
ASSERT('sake force recon "compile objects"', out, expected)


##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects
out, err = run(SAKE_CMD + '  -F "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -w -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target ensure version match
./ensure_version_match.sh
"""
experr = """cat: qstats-documentation.html: No such file or directory
./ensure_version_match.sh: line 6: [: 1.0: unary operator expected
File 'qstats-documentation.html' could not be read! Exiting!
"""
if out != expected and err != experr:
    FAIL('sake force "compile objects" failed!')


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run(SAKE_CMD + " ")
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -w -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Running target generate html documentation
pandoc -f markdown -t html qstats.md -o qstats-documentation.html
Running target ensure version match
./ensure_version_match.sh
Running target output version text file
bash -c "cat <(echo -n 'qstats version ') <(cat qstats-documentation.html | grep version | perl -pe 's/.*version (.+?)\)<.*/\\1/') | figlet > VERSION.txt"
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
ASSERT("sake build full", out, expected)
ASSERT_FILES("sake build full", True)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake build full / qstats output", out, "3\n")

##!!!!   also just tar
##################################
#  delete binary and sake recon  #
##################################
# confirm that only "build binary" and "package it" is to be rerun
os.remove("qstats")
out, err = run(SAKE_CMD + "  -r")
ASSERT("delete binary and sake recon", out, "Would run target: build binary\nWould run target: package it\n")


############################
#  delete binary and sake  #
############################
# confirm that only "build binary" is rerun
# package it isn't run because the hash is the same!
out, err = run(SAKE_CMD + " ")
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Done
"""
ASSERT("delete binary and sake", out, expected)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("delete binary and sake / qstats output", out, "3\n")


####################################
#  touch statfuncs and sake recon  #
####################################
# confirm that nothing will be rerun
os.utime("./statfuncs.c", None)
out, err = run(SAKE_CMD + "  -r")
ASSERT("touch statfuncs and sake recon", out, "")


###################################
#  edit statfuncs and sake recon  #
###################################
# it is a trivial edit so only statfuncs.c should be recompiled
shutil.copy("./statfuncs.c", "./BACKUPstatfuncs.c")
with io.open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs += "\n\n"
os.remove("./statfuncs.c")
with io.open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run(SAKE_CMD + "  -r")
ASSERT("edit statfuncs and sake recon", out, "Would run target: compile statfuncs\n")


#############################
#  edit statfuncs and sake  #
#############################
out, err = run(SAKE_CMD + " ")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Done
"""
ASSERT("edit statfuncs and sake", out, expected)


#######################################
#  big edit statfuncs and sake recon  #
#######################################
# this is a non-trivial change that will change the
# object file. it will cause a rebuilding of the
# binary but recon will not know that
with io.open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs = statfuncs.replace("return(mean);", "return(1);")
with io.open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run(SAKE_CMD + "  -r")
ASSERT("big edit statfuncs and sake recon", out, "Would run target: compile statfuncs\n")


################################
#  big edit statfuncs and sake #
################################
# statfuncs should be recompiled AND qstats should be relinked AND
# it should be repackaged
out, err = run(SAKE_CMD + " ")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
ASSERT("big edit statfuncs and sake", out, expected)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("big edit statfuncs and sake / qstats output", out, "1\n")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


###########################
#  sake quiet build full  #
###########################
# let's make sure it builds everything
out, err = run(SAKE_CMD + "  -q")
expected = """Running target compile graphfuncs
Running target compile infuncs
Running target compile qstats driver
Running target compile statfuncs
Running target build binary
Running target generate html documentation
Running target ensure version match
Running target output version text file
Running target package it
Done
"""
ASSERT("sake quiet build full", out, expected)
ASSERT_FILES("sake quiet build full", True)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake quiet build full / qstats output", out, "3\n")


###############
#  sake help  #
###############
out, err = run(SAKE_CMD + "  help")
expected = """You can 'sake' one of the following...

"build binary":
  - uses the object files and compiles the final qstats binary

"compile objects":
  - compile all c files into object files

    "compile graphfuncs":
      -  compiles the graphing functions

    "compile infuncs":
      -  compiles the input functions

    "compile qstats driver":
      -  compiles the qstats driver c program

    "compile statfuncs":
      -  compiles the statistics functions

"ensure version match":
  - this is to ensure that the version from qstats.c matches the version in the html output

"generate html documentation":
  - uses pandoc to generate html documentation from markdown

"output wrapper":
  - this is a wrapper around 'output version text file' to appropriately test the entire API

    "output version text file":
      -  this is a silly target that outputs the qstats version ascii-art printed, it is needed to test the whole API

"package it":
  - takes the final binary and documentation and puts it in a tarball

clean:
  -  remove all targets' outputs and start from scratch

visual:
  -  output visual representation of project's dependencies

"""
ASSERT("sake help", out, expected)


#########################################
#  break target with no ancestors sake  #
#########################################
# this will cause an error building the
# target "compile statfuncs" which has children
# but no ancestors
shutil.copy("./statfuncs.c", "./BACKUPstatfuncs.c")
with io.open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs = statfuncs.replace("#include <float.h>",
                              '#include <float.h>\n#include <deadcandance.h>')
with io.open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + " ")
expected = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^
1 error generated.
Command failed to run
"""
expected2 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
 #include <deadcandance.h>
                          ^
compilation terminated.
Command failed to run
"""
expected3 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
compilation terminated.
Command failed to run
"""
expected4 = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^~~~~~~~~~~~~~~~
1 error generated.
Command failed to run
"""

# if err != expected and err != expected2 and err != expected3 and err != expected4:
#     FAIL("break target with no ancestors sake failed!")
# out, err = run(SAKE_CMD + "  -r")
# expected = """Would run target: compile statfuncs
# Would run target: build binary
# Would run target: generate html documentation
# Would run target: ensure version match
# Would run target: output version text file
# Would run target: package it
# """
# if out != expected:
#     FAIL("break target with no ancestors sake failed!")
# passed("break target with no ancestors sake")


##################################################
#  break target with no ancestors sake parallel  #
##################################################
# making sure breaking behavior is correct when parallel building
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + "  -p")
expected = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^
1 error generated.
Target 'compile statfuncs' failed!
A command failed to run
"""
expected2 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
 #include <deadcandance.h>
                          ^
compilation terminated.
Target 'compile statfuncs' failed!
A command failed to run
"""
expected3 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
compilation terminated.
Target 'compile statfuncs' failed!
A command failed to run
"""
expected4 = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^~~~~~~~~~~~~~~~
1 error generated.
Target 'compile statfuncs' failed!
A command failed to run
"""
# if err != expected and err != expected2 and err != expected3 and err != expected4:
#     FAIL("break target with no ancestors sake parallel failed!")
# expected = "Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel\n"
# if out != expected:
#     FAIL("break target with no ancestors sake parallel failed!")
# out, err = run(SAKE_CMD + "  -r -p")
# expected = """Would run target 'compile statfuncs'
# Would run targets 'build binary, generate html documentation' in parallel
# Would run targets 'ensure version match, output version text file, package it' in parallel
# """
# if out != expected:
#     FAIL("break target with no ancestors sake parallel failed!")
# passed("break target with no ancestors sake parallel")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#################################
#  edit documentation and sake  #
#################################
# should only rerun "generate html documentation",
#   "ensure version match", "output version text file", and "package it"
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + " ")
shutil.copy("./qstats.md", "./BACKUPqstats.md")
with io.open("./qstats.md", "r") as fh:
    themd = fh.read()
themd = themd.replace("NAME", 'NOMBRE')
with io.open("./qstats.md", "w") as fh:
    fh.write(themd)

out, err = run(SAKE_CMD + "  -r")
ASSERT("edit documentation and sake recon", out, "Would run target: generate html documentation\n")
out, err = run(SAKE_CMD + " ")
expected = """Running target generate html documentation
pandoc -f markdown -t html qstats.md -o qstats-documentation.html
Running target ensure version match
./ensure_version_match.sh
Running target output version text file
bash -c "cat <(echo -n 'qstats version ') <(cat qstats-documentation.html | grep version | perl -pe 's/.*version (.+?)\)<.*/\\1/') | figlet > VERSION.txt"
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
ASSERT("edit documentation and sake", out, expected)

## MOVE BACK GOOD qstats.md
shutil.move("./BACKUPqstats.md", "./qstats.md")


####################
#  quiet parallel  #
####################
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + "  -p -q")
expected = """Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Going to run these targets 'build binary, generate html documentation' in parallel
Going to run these targets 'ensure version match, output version text file, package it' in parallel
Done
"""
ASSERT("quiet parallel", out, expected)


#################
#  quiet error  #
#################
shutil.copy("./statfuncs.c", "./BACKUPstatfuncs.c")
with io.open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs = statfuncs.replace("#include <float.h>",
                              '#include <float.h>\n#include <deadcandance.h>')
with io.open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + "  -q")
expected = """Running target compile graphfuncs
Running target compile infuncs
Running target compile qstats driver
Running target compile statfuncs
"""
ASSERT("quiet error stdout", out, expected)
expected = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^
1 error generated.

Command failed to run
"""
expected2 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
 #include <deadcandance.h>
                          ^
compilation terminated.

Command failed to run
"""
expected3 = """statfuncs.c:30:26: fatal error: deadcandance.h: No such file or directory
compilation terminated.

Command failed to run
"""
expected4 = """statfuncs.c:30:10: fatal error: 'deadcandance.h' file not found
#include <deadcandance.h>
         ^~~~~~~~~~~~~~~~
1 error generated.

Command failed to run
"""
# if err != expected and err != expected2 and err != expected3 and err != expected4:
#     FAIL("quiet error failed!")
# passed("quiet error")


##########################
#  quiet error parallel  #
##########################
out, err = run(SAKE_CMD + "  clean")
out, err = run(SAKE_CMD + "  -q -p")
expected = "Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel\n"
ASSERT("quiet error parallel", out, expected)
expected = """Target 'compile statfuncs' failed!
A command failed to run
"""
# if err != expected:
#     FAIL("quiet error parallel failed!")
# passed("quiet error parallel")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#############################
#  sake visual no graphviz  #
#############################
out, err = run(SAKE_CMD + "  visual -n")
expected = """strict digraph DependencyDiagram {
"build binary" -> "package it";
"compile graphfuncs" -> "build binary";
"compile infuncs" -> "build binary";
"compile qstats driver" -> "build binary";
"compile statfuncs" -> "build binary";
"generate html documentation" -> "ensure version match";
"generate html documentation" -> "output version text file";
"generate html documentation" -> "package it";
"build binary"
"compile graphfuncs"
"compile infuncs"
"compile qstats driver"
"compile statfuncs"
"ensure version match"
"generate html documentation"
"output version text file"
"package it"
}"""
with io.open("dependencies", "r") as fh:
    dotfile = fh.read()
ASSERT("sake visual no graphviz", dotfile, expected)
os.remove("dependencies")


#############################################
#  sake visual no graphviz custom filename  #
#############################################
out, err = run(SAKE_CMD + "  visual -n -f custom.dot")
expected = """strict digraph DependencyDiagram {
"build binary" -> "package it";
"compile graphfuncs" -> "build binary";
"compile infuncs" -> "build binary";
"compile qstats driver" -> "build binary";
"compile statfuncs" -> "build binary";
"generate html documentation" -> "ensure version match";
"generate html documentation" -> "output version text file";
"generate html documentation" -> "package it";
"build binary"
"compile graphfuncs"
"compile infuncs"
"compile qstats driver"
"compile statfuncs"
"ensure version match"
"generate html documentation"
"output version text file"
"package it"
}"""
with io.open("custom.dot", "r") as fh:
    dotfile = fh.read()
ASSERT("sake visual no graphviz custom filename", dotfile, expected)
os.remove("custom.dot")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


#########################################
#  sake build full CFLAGS cli override  #
#########################################
# let's make sure it builds everything with correct
# behavior for -D cli macro overrides
out, err = run(SAKE_CMD + '  -D CFLAGS="-w -O3 -I./include"')
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O3 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O3 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -w -O3 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O3 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O3 -I./include -lm
Running target generate html documentation
pandoc -f markdown -t html qstats.md -o qstats-documentation.html
Running target ensure version match
./ensure_version_match.sh
Running target output version text file
bash -c "cat <(echo -n 'qstats version ') <(cat qstats-documentation.html | grep version | perl -pe 's/.*version (.+?)\)<.*/\\1/') | figlet > VERSION.txt"
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
ASSERT("sake build full CFLAGS cli override", out, expected)
ASSERT_FILES("sake build full CFLAGS cli override", True)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake build full CFLAGS cli override / qstats output", out, "3\n")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run(SAKE_CMD + "  clean")
ASSERT("sake clean full", out, "All clean\n")
ASSERT_FILES("sake clean full", False)


##################################
#  sake recon parallel wildcard  #
##################################
# the wildcard one can't build the object files in parallel
# let's verify that
out, err = run(SAKE_CMD + '  -s wildcard-Sakefile.yaml -r -p')
expected = """Would run target 'compile c files'
Would run target 'link all objects'
"""
ASSERT("sake recon parallel wildcard", out, expected)


#######################################
#  sake build full wildcard sakefile  #
#######################################
# let's make sure it builds the wildcard sakefile correctly
out, err = run(SAKE_CMD + '  -s wildcard-Sakefile.yaml')
expected = """Running target compile c files
gcc -c -o statfuncs.o statfuncs.c -O2 -I./include; gcc -c -o graphfuncs.o graphfuncs.c -O2 -I./include; gcc -c -o infuncs.o infuncs.c -O2 -I./include; gcc -c -o qstats.o qstats.c -O2 -I./include;
Running target link all objects
gcc -o qstats qstats.o infuncs.o graphfuncs.o statfuncs.o -O2 -I./include -lm
Done
"""
ASSERT("sake build full wildcard sakefile", out, expected)
ASSERT_FILES("sake build full wildcard sakefile", True, WILDCARD_BUILD_FILES)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake build full wildcard sakefile / qstats output", out, "3\n")



##############################
#  sake clean wildcard full  #
##############################
# confirm removes everything
out, err = run(SAKE_CMD + "  -s wildcard-Sakefile.yaml clean")
ASSERT("sake clean wildcard full", out, "All clean\n")
ASSERT_FILES("sake clean wildcard full", False, WILDCARD_BUILD_FILES)



########################
#  sake patterns help  #
########################
out, err = run(SAKE_CMD + "  -s pattern-sakefile.yaml help")
expected = """You can 'sake' one of the following...

"build binary":
  - uses the object files and compiles the final qstats binary

"compile graphfuncs":
  - compile all c files (graphfuncs) into object files

"compile infuncs":
  - compile all c files (infuncs) into object files

"compile qstats":
  - compile all c files (qstats) into object files

"compile statfuncs":
  - compile all c files (statfuncs) into object files

clean:
  -  remove all targets' outputs and start from scratch

visual:
  -  output visual representation of project's dependencies

"""
ASSERT("sake patterns help", out, expected)


##################################
#  sake recon parallel patterns  #
##################################
# the patterns sakefile can build the object files in parallel
# (even though it only looks like one target)
# let's verify that
out, err = run(SAKE_CMD + '  -s pattern-sakefile.yaml -r -p')
expected = """Would run targets 'compile graphfuncs, compile infuncs, compile qstats, compile statfuncs' in parallel
Would run target 'build binary'
"""
ASSERT("sake recon parallel patterns", out, expected)


######################################
#  sake build full pattern sakefile  #
######################################
# let's make sure it builds the pattern sakefile correctly
out, err = run(SAKE_CMD + '  -s pattern-sakefile.yaml')
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -w -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -w -O2 -I./include
Running target compile qstats
gcc -c -o qstats.o qstats.c -w -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Done
"""
ASSERT("sake build full pattern sakefile", out, expected)
ASSERT_FILES("sake build full pattern sakefile", True, WILDCARD_BUILD_FILES)
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
ASSERT("sake build full pattern sakefile / qstats output", out, "3\n")



# wildcard can't build in parallel
# patterns can build in parallel



##################################
#  sake visual graphviz formats  #
##################################
# skip this if we are in travis ci because it's too much trouble
if platform.system() == 'Linux':
    sys.exit(0)
# out, err = run(SAKE_CMD + "  visual")
# if "7d2c2f6cbd52e64979d51b8fa39e5b29c5781529" != get_sha('dependencies.svg'):
#     FAIL("sake visual graphviz svg failed!")
# passed("sake visual graphviz svg")
# os.remove("./dependencies.svg")
#
# out, err = run(SAKE_CMD + "  visual -f deps")
# if "0ed2137c293d7f04db3dde87bed6487721e7ae62" != get_sha('deps.svg'):
#     FAIL("sake visual graphviz custom svg failed!")
# passed("sake visual graphviz custom svg")
# os.remove("./deps.svg")
#
# out, err = run(SAKE_CMD + "  visual -f deps.jpg")
# if "a799b75804a850c7a84424a3a3191b6357655556" != get_sha('deps.jpg'):
#     FAIL("sake visual graphviz custom jpg failed!")
# passed("sake visual graphviz custom jpg")
# os.remove("./deps.jpg")
#
# out, err = run(SAKE_CMD + "  visual -f deps.jpeg")
# if "a799b75804a850c7a84424a3a3191b6357655556" != get_sha('deps.jpeg'):
#     FAIL("sake visual graphviz custom jpeg failed!")
# passed("sake visual graphviz custom jpeg")
# os.remove("./deps.jpeg")
#
# out, err = run(SAKE_CMD + "  visual -f deps.png")
# if "05d908d6cc619503466b7d7b1798bfae7154b046" != get_sha('deps.png'):
#     FAIL("sake visual graphviz custom png failed!")
# passed("sake visual graphviz custom png")
# os.remove("./deps.png")
#
# out, err = run(SAKE_CMD + "  visual -f deps.gif")
# if "e0cea15a115d98105f80b30f4f4910a841654e79" != get_sha('deps.gif'):
#     FAIL("sake visual graphviz custom gif failed!")
# passed("sake visual graphviz custom gif")
# os.remove("./deps.gif")
#
# out, err = run(SAKE_CMD + "  visual -f deps.ps")
# if "76506d3d1a329c8d2c8f3f43bfb6a787b0571b97" != get_sha('deps.ps'):
#     FAIL("sake visual graphviz custom ps failed!")
# passed("sake visual graphviz custom ps")
# os.remove("./deps.ps")
#
# out, err = run(SAKE_CMD + "  visual -f deps.pdf")
# if "5a1a729eaf18d4e8bb8d414f22e6a4dc93fdd7db" != get_sha('deps.pdf'):
#     FAIL("sake visual graphviz custom pdf failed!")
# passed("sake visual graphviz custom pdf")
# os.remove("./deps.pdf")


###------
# confirm sake visual no graphiz custom filename
# sake visual
# sake visual other formats
#
# most recent bug fixes
# get rid of tar.gz and rebuild
