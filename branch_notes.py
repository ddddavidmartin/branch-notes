#! /usr/bin/env python3

# Open and edit notes for the given git branch.

import argparse
import os
import re
import subprocess
import sys


# Environment variable name that is used to specify the notes directory.
NOTES_DIR_VARIABLE = 'NOTES_DIR'

RESULT_SUCCESS = 0
RESULT_ERROR = 1

BRANCH_OPTION = 'branch'
TOPLEVEL_OPTION = '--toplevel'
CURRENT_BRANCH_OPTION = '-'


def main():
    descr = ("Open and edit notes for the given branch. "
             "By default a notes file is created under "
             "'NOTES_DIR/toplevel/branch.txt'. NOTES_DIR is read from the "
             "environment variable '%s'." % NOTES_DIR_VARIABLE)
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument(BRANCH_OPTION, type=str,
                        help=("The branch to use. Specifiy '%s' to use the "
                              "current git branch." % CURRENT_BRANCH_OPTION))
    parser.add_argument(TOPLEVEL_OPTION, type=str,
                        help=("The project directory name under which the "
                              "notes file for the given branch is created."))
    options = parser.parse_args()

    if options.branch != CURRENT_BRANCH_OPTION and not options.toplevel:
        print("'%s' has to be specified when '%s' is not '%s'." %
              (TOPLEVEL_OPTION, BRANCH_OPTION, CURRENT_BRANCH_OPTION))
        return RESULT_ERROR


    # If CURRENT_BRANCH_OPTION is provided as the target branch we use the
    # current git branch.
    if options.branch == CURRENT_BRANCH_OPTION:
        branch = ""
        git_cmd = ['git', 'symbolic-ref', '--short', 'HEAD']
        try:
            branch = subprocess.check_output(git_cmd, encoding='UTF-8').rstrip()
        except subprocess.CalledProcessError as e:
            print("Failed to determine git branch from current dir: %s" % e)
            return RESULT_ERROR

        p = re.compile(r'^p4/(tasks|spfw)/')
        branch = p.sub('', branch)

    else:
        branch = options.branch

    if options.toplevel:
        toplevel = options.toplevel
    else:
        git_cmd = ['git', 'rev-parse', '--show-toplevel']
        try:
            toplevel = subprocess.check_output(git_cmd, encoding='UTF-8').rstrip()
        except subprocess.CalledProcessError as e:
            print("Failed to determine git toplevel from current dir: %s" % e)
            return RESULT_ERROR
        toplevel = os.path.basename(toplevel)

    try:
        # It is necessary to expand a tilde in the as otherwise the following
        # os.makedirs call creates a directory called '~'.
        notes_dir = os.path.expanduser(os.environ[NOTES_DIR_VARIABLE])
    except KeyError as e:
        print("Failed to determine notes directory. Set in environment variable "
              "'%s'." % NOTES_DIR_VARIABLE)
        return RESULT_ERROR
    notes_dir = notes_dir + '/' + toplevel
    # Instead of checking whether a directory exists, we simply create it if
    # necessary and allow for it to exist already.
    os.makedirs(notes_dir, exist_ok=True)

    notes_file = notes_dir + '/' + branch + '.txt'

    editor_cmd = ['vim', notes_file]
    try:
        subprocess.run(editor_cmd)
    except subprocess.CalledProcessError as e:
        print("Failed to run editor: %s" % e)
        return RESULT_ERROR

if __name__ == '__main__':
    sys.exit(main())
