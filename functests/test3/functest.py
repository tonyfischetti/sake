#!/usr/bin/env python -tt

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


here = os.path.dirname(__file__)
os.chdir(here)

## !!!!!!!!!!! change directory later


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
    return out.decode(encoding), err.decode(encoding)

def passed(whichtest):
    print("{:>45} {:>15}".format(whichtest, "\033[92mpassed\033[0m"))

##################
#  start clean  ##
##################
# let's start off clean
out, err = run("../../sake clean")
# not relying on it being clean or not
### check for any file
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./VERSION.txt") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("start clean failed!")
passed("start clean")


######################
#  sake recon full  ##
######################
# let's make sure it says it should build all targets
## RECON STILL MAKES .shastore!
out, err = run("../../sake -r")
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
if out != expected:
    FAIL("sake recon full failed!")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile("qstats") or os.path.isfile("./VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake recon full failed!")
passed("sake recon full")


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run("../../sake")
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
if out != expected:
    FAIL("sake build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("./VERSION.txt") or
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full failed!")
passed("sake build full")


#####################
#  sake recon full  #
#####################
# confirm it says nothing should be built
out, err = run("../../sake -r")
if out:
    FAIL("sake recon full failed!")
passed("sake recon full")


######################
#  sake build full  ##
######################
# confirm nothing happens
out, err = run("../../sake")
if out != "Done\n":
    FAIL("sake build full failed!")
passed("sake build full")


###########################
#  sake recon clean full  #
###########################
# confirm would remove everything but doesn't
out, err = run("../../sake -r clean")
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
if out != expected:
    FAIL("sake recon clean full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("VERSION.txt") or 
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake recon clean full failed!")
passed("sake recon clean full")



#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


##############################
## sake recon parallel full  #
##############################
# confirm would run everything and compile all
# objects in parallel
out, err = run("../../sake -r -p")
expected = """Would run targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Would run targets 'build binary, generate html documentation' in parallel
Would run targets 'ensure version match, output version text file, package it' in parallel
"""
if out != expected:
    FAIL("sake recon parallel full failed!")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile("qstats") or
    os.path.isfile("./VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake recon parallel full failed!")
passed("sake recon parallel full")


########################
## sake parallel full  #
########################
# confirm builds all and builds correctly
out, err = run("../../sake -p")
expected = """Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Going to run these targets 'build binary, generate html documentation' in parallel
Going to run these targets 'ensure version match, output version text file, package it' in parallel
Done
"""
if out != expected:
    FAIL("sake parallel full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("./VERSION.txt") or
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake parallel full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake parallel full failed!")
passed("sake parallel full")


##########################
#  sake "build twinary"  #
##########################
# confirm that it errors and says there is no such target
out, err = run('../../sake "build twinary"')
if err != "Error: Couldn't find target 'build twinary' in Sakefile\n":
    FAIL('sake "build twinary"')
passed('sake "build twinary"')


#########################
#  sake "build binary"  #
#########################
# confirm that it doesn't build
out, err = run('../../sake "build binary"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Done
"""
if out != expected:
    FAIL('sake "build binary" failed!')
passed('sake "build binary"')


###############################
#  sake force "build binary"  #
###############################
# confirm that it forces a build of binary
out, err = run('../../sake -F "build binary"')
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL('sake force "build binary" failed!')
passed('sake force "build binary"')


##################################
#  sake recon "compile objects"  #
##################################
# won't do anything
##### 
##### BUT DO MORE THINGS NEED TO BE ADDED TO "DONT UPDATE"?
##### 
##### 
out, err = run('../../sake clean')
out, err = run('../../sake')
out, err = run('../../sake -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
"""
if out != expected:
    FAIL('sake recon "compile objects" failed!')
passed('sake recon "compile objects"')


########################################
#  sake force recon "compile objects"  #
########################################
out, err = run('../../sake -F -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
Would run target: ensure version match
"""
if out != expected:
    FAIL('sake force recon "compile objects" failed!')
passed('sake force recon "compile objects"')


##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects
out, err = run('../../sake -F "compile objects"')
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
if out != expected:
    FAIL('sake force "compile objects" failed!')
passed('sake force "compile objects"')


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


########################################
#  sake force recon "compile objects"  #
########################################
out, err = run('../../sake -F -r "compile objects"')
expected = """The following targets share dependencies and must be run together:
  - compile qstats driver
  - ensure version match
Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
Would run target: ensure version match
"""
if out != expected:
    FAIL('sake force recon "compile objects" failed!')
passed('sake force recon "compile objects"')


##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects
out, err = run('../../sake -F "compile objects"')
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
passed('sake force "compile objects"')


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("./VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run("../../sake")
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
if out != expected:
    FAIL("sake build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("./VERSION.txt") or
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full failed!")
passed("sake build full")

##!!!!   also just tar
##################################
#  delete binary and sake recon  #
##################################
# confirm that only "build binary" and "package it" is to be rerun
os.remove("qstats")
out, err = run("../../sake -r")
if out != "Would run target: build binary\nWould run target: package it\n":
    FAIL("delete binary and sake recon failed!")
passed("delete binary and sake recon")


############################
#  delete binary and sake  #
############################
# confirm that only "build binary" is rerun
# package it isn't run because the hash is the same!
out, err = run("../../sake")
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("delete binary and sake failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("delete binary and sake failed!")
passed("delete binary and sake")


####################################
#  touch statfuncs and sake recon  #
####################################
# confirm that nothing will be rerun
os.utime("./statfuncs.c", None)
out, err = run("../../sake -r")
if out:
    FAIL("touch statfuncs and sake recon failed!")
passed("touch statfuncs and sake recon")


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
out, err = run("../../sake -r")
if out != "Would run target: compile statfuncs\n":
    FAIL("edit statfuncs and sake recon failed!")
passed("edit statfuncs and sake recon")


#############################
#  edit statfuncs and sake  #
#############################
out, err = run("../../sake")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Done
"""
if out != expected:
    FAIL("edit statfuncs and sake failed!")
passed("edit statfuncs and sake")


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
out, err = run("../../sake -r")
if out != "Would run target: compile statfuncs\n":
    FAIL("big edit statfuncs and sake recon failed!")
passed("big edit statfuncs and sake recon")


################################
#  big edit statfuncs and sake #
################################
# statfuncs should be recompiled AND qstats should be relinked AND
# it should be repackaged
out, err = run("../../sake")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -w -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -w -O2 -I./include -lm
Running target package it
mkdir qstats-v1.0; cp qstats qstats-v1.0; cp qstats-documentation.html qstats-v1.0; tar cvfz qstats.tar.gz qstats-v1.0 > /dev/null 2>&1; rm -rf qstats-v1.0;
Done
"""
if out != expected:
    FAIL("big edit statfuncs and sake failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "1\n":
    FAIL("big edit statfuncs and sake failed!")
passed("big edit statfuncs and sake")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("./VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


###########################
#  sake quiet build full  #
###########################
# let's make sure it builds everything
out, err = run("../../sake -q")
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
if out != expected:
    FAIL("sake quiet build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("./VERSION.txt") or
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake quiet build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake quiet build full failed!")
passed("sake quiet build full")


###############
#  sake help  #
###############
out, err = run("../../sake help")
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
if out != expected:
    FAIL("sake help failed!")
passed("sake help")


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
out, err = run("../../sake clean")
out, err = run("../../sake")
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
if err != expected and err != expected2 and err != expected3:
    FAIL("break target with no ancestors sake failed!")
out, err = run("../../sake -r")
expected = """Would run target: compile statfuncs
Would run target: build binary
Would run target: generate html documentation
Would run target: ensure version match
Would run target: output version text file
Would run target: package it
"""
if out != expected:
    FAIL("break target with no ancestors sake failed!")
passed("break target with no ancestors sake")


##################################################
#  break target with no ancestors sake parallel  #
##################################################
# making sure breaking behavior is correct when parallel building
out, err = run("../../sake clean")
out, err = run("../../sake -p")
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
if err != expected and err != expected2 and err != expected3:
    FAIL("break target with no ancestors sake parallel failed!")
expected = "Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel\n"
if out != expected:
    FAIL("break target with no ancestors sake parallel failed!")
out, err = run("../../sake -r -p")
expected = """Would run target 'compile statfuncs'
Would run targets 'build binary, generate html documentation' in parallel
Would run targets 'ensure version match, output version text file, package it' in parallel
"""
if out != expected:
    FAIL("break target with no ancestors sake parallel failed!")
passed("break target with no ancestors sake parallel")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#################################
#  edit documentation and sake  #
#################################
# should only rerun "generate html documentation",
#   "ensure version match", "output version text file", and "package it"
out, err = run("../../sake clean")
out, err = run("../../sake")
shutil.copy("./qstats.md", "./BACKUPqstats.md")
with io.open("./qstats.md", "r") as fh:
    themd = fh.read()
themd = themd.replace("NAME", 'NOMBRE')
with io.open("./qstats.md", "w") as fh:
    fh.write(themd)

out, err = run("../../sake -r")
if out != "Would run target: generate html documentation\n":
    FAIL("edit documentation and sake failed!")
out, err = run("../../sake")
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
if out != expected:
    FAIL("edit documentation and sake failed!")
passed("edit documentation and sake")

## MOVE BACK GOOD qstats.md
shutil.move("./BACKUPqstats.md", "./qstats.md")


####################
#  quiet parallel  #
####################
out, err = run("../../sake clean")
out, err = run("../../sake -p -q")
expected = """Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Going to run these targets 'build binary, generate html documentation' in parallel
Going to run these targets 'ensure version match, output version text file, package it' in parallel
Done
"""
if out != expected:
    FAIL("quiet parallel failed")
passed("quiet parallel")


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
out, err = run("../../sake clean")
out, err = run("../../sake -q")
expected = """Running target compile graphfuncs
Running target compile infuncs
Running target compile qstats driver
Running target compile statfuncs
"""
if out != expected:
    FAIL("quiet error failed!")
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
if err != expected and err != expected2 and err != expected3:
    FAIL("quiet error failed!")
passed("quiet error")


##########################
#  quiet error parallel  #
##########################
out, err = run("../../sake clean")
out, err = run("../../sake -q -p")
expected = "Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel\n"
if out != expected:
    FAIL("quiet error parallel failed!")
expected = """Target 'compile statfuncs' failed!
A command failed to run
"""
if err != expected:
    FAIL("quiet error parallel failed!")
passed("quiet error parallel")

## MOVE BACK GOOD STATFUNCS.c
shutil.move("./BACKUPstatfuncs.c", "./statfuncs.c")


#############################
#  sake visual no graphviz  #
#############################
out, err = run("../../sake visual -n")
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
if dotfile != expected:
    FAIL("sake visual no graphviz failed!")
passed("sake visual no graphviz")
os.remove("dependencies")


#############################################
#  sake visual no graphviz custom filename  #
#############################################
out, err = run("../../sake visual -n -f custom.dot")
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
if dotfile != expected:
    FAIL("sake visual no graphviz custom filename failed!")
passed("sake visual no graphviz custom filename")
os.remove("custom.dot")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


#########################################
#  sake build full CFLAGS cli override  #
#########################################
# let's make sure it builds everything with correct
# behavior for -D cli macro overrides
out, err = run('../../sake -D CFLAGS="-w -O3 -I./include"')
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
if out != expected:
    FAIL("sake build full CFLAGS cli override failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats") or
    not os.path.isfile("./VERSION.txt") or
    not os.path.isfile("qstats-documentation.html") or not os.path.isfile("qstats.tar.gz")):
    FAIL("sake build full CFLAGS cli override failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full CFLAGS cli override failed!")
passed("sake build full CFLAGS cli override")


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats") or
    os.path.isfile("VERSION.txt") or
    os.path.isfile("qstats-documentation.html") or os.path.isfile("qstats.tar.gz")):
    FAIL("sake clean full failed")
passed("sake clean full")


##################################
#  sake recon parallel wildcard  #
##################################
# the wildcard one can't build the object files in parallel
# let's verify that
out, err = run('../../sake -s wildcard-Sakefile.yaml -r -p')
expected = """Would run target 'compile c files'
Would run target 'link all objects'
"""
if out != expected:
    FAIL("sake recon parallel wildcard failed!")
passed("sake recon parallel wildcard")


#######################################
#  sake build full wildcard sakefile  #
#######################################
# let's make sure it builds the wildcard sakefile correctly
out, err = run('../../sake -s wildcard-Sakefile.yaml')
expected = """Running target compile c files
gcc -c -o statfuncs.o statfuncs.c -O2 -I./include; gcc -c -o graphfuncs.o graphfuncs.c -O2 -I./include; gcc -c -o infuncs.o infuncs.c -O2 -I./include; gcc -c -o qstats.o qstats.c -O2 -I./include;
Running target link all objects
gcc -o qstats qstats.o infuncs.o graphfuncs.o statfuncs.o -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("sake build full wildcard sakefile failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake build full wildcard sakefile failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full wildcard sakefile failed!")
passed("sake build full wildcard sakefile override")



##############################
#  sake clean wildcard full  #
##############################
# confirm removes everything
out, err = run("../../sake -s wildcard-Sakefile.yaml clean")
if out != "All clean\n":
    FAIL("sake clean wildcard full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("sake clean wildcard full failed")
passed("sake clean wildcard full")



########################
#  sake patterns help  #
########################
out, err = run("../../sake -s pattern-sakefile.yaml help")
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
if out != expected:
    FAIL("sake patterns help failed!")
passed("sake patterns help")


##################################
#  sake recon parallel patterns  #
##################################
# the patterns sakefile can build the object files in parallel
# (even though it only looks like one target)
# let's verify that
out, err = run('../../sake -s pattern-sakefile.yaml -r -p')
expected = """Would run targets 'compile graphfuncs, compile infuncs, compile qstats, compile statfuncs' in parallel
Would run target 'build binary'
"""
if out != expected:
    FAIL("sake recon parallel patterns failed!")
passed("sake recon parallel patterns")


######################################
#  sake build full pattern sakefile  #
######################################
# let's make sure it builds the pattern sakefile correctly
out, err = run('../../sake -s pattern-sakefile.yaml')
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
if out != expected:
    FAIL("sake build full pattern sakefile failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake build full pattern sakefile failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full pattern sakefile failed!")
passed("sake build full pattern sakefile override")



# wildcard can't build in parallel
# patterns can build in parallel



##################################
#  sake visual graphviz formats  #
##################################
# skip this if we are in travis ci because it's too much trouble
if platform.system() == 'Linux':
    sys.exit(0)
# out, err = run("../../sake visual")
# if "7d2c2f6cbd52e64979d51b8fa39e5b29c5781529" != get_sha('dependencies.svg'):
#     FAIL("sake visual graphviz svg failed!")
# passed("sake visual graphviz svg")
# os.remove("./dependencies.svg")
#
# out, err = run("../../sake visual -f deps")
# if "0ed2137c293d7f04db3dde87bed6487721e7ae62" != get_sha('deps.svg'):
#     FAIL("sake visual graphviz custom svg failed!")
# passed("sake visual graphviz custom svg")
# os.remove("./deps.svg")
#
# out, err = run("../../sake visual -f deps.jpg")
# if "a799b75804a850c7a84424a3a3191b6357655556" != get_sha('deps.jpg'):
#     FAIL("sake visual graphviz custom jpg failed!")
# passed("sake visual graphviz custom jpg")
# os.remove("./deps.jpg")
#
# out, err = run("../../sake visual -f deps.jpeg")
# if "a799b75804a850c7a84424a3a3191b6357655556" != get_sha('deps.jpeg'):
#     FAIL("sake visual graphviz custom jpeg failed!")
# passed("sake visual graphviz custom jpeg")
# os.remove("./deps.jpeg")
#
# out, err = run("../../sake visual -f deps.png")
# if "05d908d6cc619503466b7d7b1798bfae7154b046" != get_sha('deps.png'):
#     FAIL("sake visual graphviz custom png failed!")
# passed("sake visual graphviz custom png")
# os.remove("./deps.png")
#
# out, err = run("../../sake visual -f deps.gif")
# if "e0cea15a115d98105f80b30f4f4910a841654e79" != get_sha('deps.gif'):
#     FAIL("sake visual graphviz custom gif failed!")
# passed("sake visual graphviz custom gif")
# os.remove("./deps.gif")
#
# out, err = run("../../sake visual -f deps.ps")
# if "76506d3d1a329c8d2c8f3f43bfb6a787b0571b97" != get_sha('deps.ps'):
#     FAIL("sake visual graphviz custom ps failed!")
# passed("sake visual graphviz custom ps")
# os.remove("./deps.ps")
#
# out, err = run("../../sake visual -f deps.pdf")
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
