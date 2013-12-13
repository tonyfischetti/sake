#!/usr/bin/env python -tt

import yaml
import pudb
from subprocess import Popen, PIPE
import sys
import os.path
import hashlib



def update_these_shas(output_list):
    pass


def write_shas_to_persistent_file(sha_dict):
    fh = open(".shastore", "w")
    fh.write("%YAML 1.2\n---\n\n")
    for key in sha_dict:
        fh.write("{}: {}\n".format(key, sha_dict[key]))
    fh.write("\n...")


def take_shas_of_all_dependencies():
    # only the dependencies from targets in all
    sha_dict = {}
    all_deps = []
    for target in sakefile['all']:
        print target
        if 'dependencies' in sakefile[target]:
            print "Dependencies are in it"
            for dep in sakefile[target]['dependencies']:
                print "dep: " + dep
                all_deps.append(dep)
    if len(all_deps):
        for dep in all_deps:
            if os.path.isfile(dep):
                sha_dict[dep] = hashlib.sha1(open(dep, "r").read()).hexdigest() 
        return sha_dict
    print "no dependencies" #########


def process_cli_args(args):
    for arg in args:
        print arg


def needs_to_run(target):
    if 'dependencies' not in sakefile[target]:
        print "Target {} has no dependencies and needs to run".format(target)
        # if it has no dependencies, it always needs to run
        return True
    for dep  in sakefile[target]['dependencies']:
        now_sha = hashlib.sha1(open(dep, "r").read()).hexdigest() 
        print now_sha
        print from_store
        print "!"
        if now_sha != from_store[dep]:
            print "There's a mismatch for dep {} -it needs to run".format(dep)
            return True
    return False


def run_the_target(target):
    print "Running target {}".format(target)
    run_commands(sakefile[target]['formula'])
    return


def build_target(target_name):
    if needs_to_run(target_name):
        run_commands(sakefile['target']['formula'])
        #update_these_shas(sakefile['target']['outputs'])
    return


def run_commands(commands):
    commands = commands.rstrip()
    print commands
    p = Popen(commands, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode:
        print err
        sys.exit("Command failed to run")


def build_sha_store():
    sha_dict = take_shas_of_all_dependencies()
    write_shas_to_persistent_file(sha_dict)
    from_store = yaml.load(open(".shastore", "r").read())
    current_shas = from_store


######################

sakefile = yaml.load(open("Sakefile.yaml", "r").read())

if len(sys.argv) > 1:
    process_cli_args(sys.argv[1:])
else:
    print "no args"

if not os.path.isfile(".shastore"):
    build_sha_store
else:
    # this means its there
    # that means we have to read it and check
    # to see if any of the files changed
    current_shas = take_shas_of_all_dependencies()
    from_store = yaml.load(open(".shastore", "r").read())
    if not from_store:
        ### making a function
    print from_store
    if current_shas == from_store:
        print "its the same"
    else:
        print "its different"
    pass

print from_store
print current_shas




# # process (all) things
print "\n\nAbout to process targets"
for target in sakefile['all']:
    print "Checking target {}".format(target)
    if needs_to_run(target):
        run_the_target(target)
#     # what if its not a target
#     # determine if it needs to run
#     for dependency in sakefile['target']['dependencies']:
# 



# all done
write_shas_to_persistent_file(current_shas)


# what if dependency isn't in the store?
# can't have a target named help
# convert all opens to opens and closese
