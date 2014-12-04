#!/usr/bin/env python -tt



#####################################
##                                 ##
##  FUNCTIONALLY TESTS ENTIRE API  ##
##                                 ##
#####################################

import os
import sys
import shutil
from subprocess import Popen, PIPE


here = os.path.dirname(__file__)
os.chdir(here)

## !!!!!!!!!!! change directory later


def FAIL(message):
    sys.stderr.write(message + "\n")
    sys.exit(1)

def run(command, spit_output=False):
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    # if p.returncode:
    #     print("Command '{}' failed!".format(command))
    #     print(err)
    #     sys.exit(1)
    if spit_output:
        print("\nTHIS WAS THE OUTPUT:\n{}\n=======".format(out.decode("utf-8")))
    return out.decode('utf-8'), err.decode('utf-8')


##################
#  start clean  ##
##################
# let's start off clean
out, err = run("../../sake clean")
# not relying on it being clean or not
### check for any file
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("start clean failed!")
print("start clean passed")


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
"""
if out != expected:
    FAIL("sake recon full failed!")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile("qstats")):
    FAIL("sake recon full failed!")
print("sake recon full passed")


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run("../../sake")
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -Wall -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -Wall -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -Wall -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("sake build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full failed!")
print("sake build full passed")


#####################
#  sake recon full  #
#####################
# confirm it says nothing should be built
out, err = run("../../sake -r")
if out:
    FAIL("sake recon full failed!")
print("sake recon full passed")


######################
#  sake build full  ##
######################
# confirm nothing happens
out, err = run("../../sake")
if out != "Done\n":
    FAIL("sake build full failed!")
print("sake build full passed")


###########################
#  sake recon clean full  #
###########################
# confirm would remove everything but doesn't
out, err = run("../../sake -r clean")
expected = """Would remove file: .shastore
Would remove file: graphfuncs.o
Would remove file: infuncs.o
Would remove file: qstats
Would remove file: qstats.o
Would remove file: statfuncs.o
"""
if out != expected:
    FAIL("sake recon clean full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake recon clean full failed!")
print("sake recon clean full passed")



#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("sake clean full failed")
print("sake clean full passed")


##############################
## sake recon parallel full  #
##############################
# confirm would run everything and compile all
# objects in parallel
out, err = run("../../sake -r -p")
expected = """Would run targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Would run target 'build binary'
"""
if out != expected:
    FAIL("sake recon parallel full failed!")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile("qstats")):
    FAIL("sake recon parallel full failed!")
print("sake recon parallel full passed")


########################
## sake parallel full  #
########################
# confirm builds all and builds correctly
out, err = run("../../sake -p")
expected = """Going to run these targets 'compile graphfuncs, compile infuncs, compile qstats driver, compile statfuncs' in parallel
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("sake parallel full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake parallel full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake parallel full failed!")
print("sake parellel full passed")


##########################
#  sake "build twinary"  #
##########################
# confirm that it errors and says there is no such target
out, err = run('../../sake "build twinary"')
if err != "Error: Couldn't find target 'build twinary' in Sakefile\n":
    FAIL('sake "build twinary"')
print('sake "build twinary" passed')


#########################
#  sake "build binary"  #
#########################
# confirm that it doesn't build
out, err = run('../../sake "build binary"')
if out != "Done\n":
    FAIL('sake "build binary" failed!')
print('sake "build binary" passed')


###############################
#  sake force "build binary"  #
###############################
# confirm that it forces a build of binary
out, err = run('../../sake -F "build binary"')
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL('sake force "build binary" failed!')
print('sake force "build binary" passed')


##################################
#  sake recon "compile objects"  #
##################################
# won't do anything
out, err = run('../../sake "compile objects"')
if out != "Done\n":
    FAIL('sake "compile objects" failed!')
print('sake "compile objects" passed')



##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects
out, err = run('../../sake -F "compile objects"')
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -Wall -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -Wall -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -Wall -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Done
"""
if out != expected:
    FAIL('sake force "compile objects" failed!')
print('sake force "compile objects" passed')


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("sake clean full failed")
print("sake clean full passed")


########################################
#  sake force recon "compile objects"  #
########################################
# corfirm would compile all objects but nothing else
out, err = run('../../sake -F -r "compile objects"')
expected = """Would run target: compile graphfuncs
Would run target: compile infuncs
Would run target: compile qstats driver
Would run target: compile statfuncs
"""
if out != expected:
    FAIL('sake force recon "compile objects" failed!')
print('sake force recon "compile objects" passed')



##################################
#  sake force "compile objects"  #
##################################
out, err = run('../../sake -F "compile objects"')
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -Wall -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -Wall -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -Wall -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Done
"""
if out != expected:
    FAIL('sake force "compile objects" failed!')
if os.path.isfile("qstats"):
    FAIL('sake force "compile objects" failed!')
print('sake force "compile objects" passed')


#####################
#  sake clean full  #
#####################
# confirm removes everything
out, err = run("../../sake clean")
if out != "All clean\n":
    FAIL("sake clean full failed")
if (os.path.isfile("./graphfuncs.o") or os.path.isfile("./infuncs.o") or
    os.path.isfile("./qstats.o") or os.path.isfile("./statfuncs.o") or
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("sake clean full failed")
print("sake clean full passed")


#####################
#  sake build full  #
#####################
# let's make sure it builds everything
out, err = run("../../sake")
expected = """Running target compile graphfuncs
gcc -c -o graphfuncs.o graphfuncs.c -Wall -O2 -I./include
Running target compile infuncs
gcc -c -o infuncs.o infuncs.c -Wall -O2 -I./include
Running target compile qstats driver
gcc -c -o qstats.o qstats.c -Wall -O2 -I./include
Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("sake build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake build full failed!")
print("sake build full passed")


##################################
#  delete binary and sake recon  #
##################################
# confirm that only "build binary" is to be rerun
os.remove("qstats")
out, err = run("../../sake -r")
if out != "Would run target: build binary\n":
    FAIL("delete binary and sake recon failed!")
print("delete binary and sake recon passed")


############################
#  delete binary and sake  #
############################
# confirm that only "build binary" is rerun
out, err = run("../../sake")
expected = """Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("delete binary and sake failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("delete binary and sake failed!")
print("delete binary and sake passed")


####################################
#  touch statfuncs and sake recon  #
####################################
# confirm that nothing will be rerun
os.utime("./statfuncs.c")
out, err = run("../../sake -r")
if out:
    FAIL("touch statfuncs and sake recon failed!")
print("touch statfuncs and sake recon passed")


###################################
#  edit statfuncs and sake recon  #
###################################
# it is a trivial edit so only statfuncs.c should be recompiled
shutil.copy("./statfuncs.c", "./BACKUPstatfuncs.c")
with open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs += "\n\n"
os.remove("./statfuncs.c")
with open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run("../../sake -r")
if out != "Would run target: compile statfuncs\n":
    FAIL("edit statfuncs and sake recon failed!")
print("edit statfuncs and sake recon passed")


#############################
#  edit statfuncs and sake  #
#############################
out, err = run("../../sake")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Done
"""
if out != expected:
    FAIL("edit statfuncs and sake failed!")
print("edit statfuncs and sake passed")


#######################################
#  big edit statfuncs and sake recon  #
#######################################
# this is a non-trivial change that will change the
# object file. it will cause a rebuilding of the
# binary but recon will not know that
with open("./statfuncs.c", "r") as fh:
    statfuncs = fh.read()
statfuncs = statfuncs.replace("return(mean);", "return(1);")
with open("./statfuncs.c", "w") as fh:
    fh.write(statfuncs)
out, err = run("../../sake -r")
if out != "Would run target: compile statfuncs\n":
    FAIL("big edit statfuncs and sake recon failed!")
print("big edit statfuncs and sake recon passed")



################################
#  big edit statfuncs and sake #
################################
# statfuncs should be recompiled AND qstats should be relinked
out, err = run("../../sake")
expected = """Running target compile statfuncs
gcc -c -o statfuncs.o statfuncs.c -Wall -O2 -I./include
Running target build binary
gcc -o qstats qstats.o statfuncs.o infuncs.o graphfuncs.o -Wall -O2 -I./include -lm
Done
"""
if out != expected:
    FAIL("big edit statfuncs and sake failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "1\n":
    FAIL("big edit statfuncs and sake failed!")
print("big edit statfuncs and sake passed")

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
    os.path.isfile(".shastore") or os.path.isfile("qstats")):
    FAIL("sake clean full failed")
print("sake clean full passed")


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
Done
"""
if out != expected:
    FAIL("sake quiet build full failed!")
if (not os.path.isfile("./graphfuncs.o") or not os.path.isfile("./infuncs.o") or
    not os.path.isfile("./qstats.o") or not os.path.isfile("./statfuncs.o") or
    not os.path.isfile(".shastore") or not os.path.isfile("qstats")):
    FAIL("sake quiet build full failed!")
out, err = run('echo "1\n2\n3\n4\n5" | ./qstats -m')
if out != "3\n":
    FAIL("sake quiet build full failed!")
print("sake quiet build full passed")


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

clean:
  -  remove all targets' outputs and start from scratch

visual:
  -  output visual representation of project's dependencies

"""
if out != expected:
    FAIL("sake help failed!")
print("sake help passed")

###------
# confirm quiet (no output)
# confirm sake help
# confirm sake visual no graphiz custom filename
# sake visual
# sake visual other formats



