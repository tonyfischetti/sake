#!/usr/bin/env python -tt



#####################################
##                                 ##
##  FUNCTIONALLY TESTS ENTIRE API  ##
##                                 ##
#####################################

import os
import sys
from subprocess import Popen, PIPE


here = os.path.dirname(__file__)
os.chdir(here)

## !!!!!!!!!!! change directory later



def run(command, spit_output=False):
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode:
        print("Command '{}' failed!".format(command))
        print(err)
        sys.exit(1)
    print("\nTHIS WAS THE OUTPUT:\n{}\n=======".format(out.decode("utf-8")))
    return out, err


### FUNCTION TO ACTUALLY CHECK SAKE WITH REAL INPUT


##################
#  start clean  ##
##################
# let's start off clean
out, err = run("../../sake clean")


######################
#  sake recon full  ##
######################
# let's make sure it says it should build all targets
out, err = run("../../sake -r")
# do it


#####################
#  sake build full  #
#####################
# let's make sure it builds everything


#####################
#  sake recon full  #
#####################
# confirm it says nothing should be built


######################
#  sake build full  ##
######################
# confirm nothing happens


###########################
#  sake recon clean full  #
###########################
# confirm would remove everything but doesn't


#####################
#  sake clean full  #
#####################
# confirm removes everything
# includes .shastore


##############################
## sake recon parallel full  #
##############################
# confirm would run everything and compile all
# ojects in parallel


########################
## sake parallel full  #
########################
# confirm builds all and builds correctly


#########################
#  sake "build binary"  #
#########################
# confirm that it doesn't build


###############################
#  sake force "build binary"  #
###############################
# confirm that it forces a build of binary


##################################
#  sake recon "compile objects"  #
##################################
# won't do anything



##################################
#  sake force "compile objects"  #
##################################
# force compile the four c files into objects


# sake clean

# sake -F -r "compile objects"

# sake -F "compile objects"

# confirm that ./qstats doesn't exist

# sake clean

# sake

# delete binary

# sake -r

# confirm that only "build binary" will be built

# sake

# sake clean

# edit statfuncs.c

# sake -r

# confirm rebuild (only?) that c file (maybe build binary, too?)


###------
# confirm quiet (no output)
# confirm sake help
# confirm sake visual no graphiz custom filename
# sake visual
# sake visual other formats
