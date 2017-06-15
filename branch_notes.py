#! /usr/bin/env python3

"""Open and edit notes for the given git branch."""

import argparse
import os
import re
import subprocess
import sys


# Environment variable name that is used to specify the notes directory.
NOTES_DIR_VARIABLE = 'NOTES_DIR'

# Generic environment variable name that is used to specify the notes editor.
EDITOR_VARIABLE = 'BRANCH_NOTES_EDITOR'

RESULT_SUCCESS = 0
RESULT_ERROR = 1

BRANCH_OPTION = 'branch'
TOPLEVEL_OPTION = '--toplevel'
CURRENT_BRANCH_OPTION = '-'

ACTIONS = ['open', 'list']


def _parse_options():
    """Parse the provided command line parameters."""
    descr = ("Open and edit notes for the given branch. "
             "By default a notes file is created under "
             "'NOTES_DIR/toplevel/branch.txt'. NOTES_DIR is read from the "
             "environment variable '%s'." % NOTES_DIR_VARIABLE)
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('action', choices=ACTIONS,
                        help=("Open note or list existing notes."))
    parser.add_argument(BRANCH_OPTION, type=str, nargs='?',
                        default=CURRENT_BRANCH_OPTION,
                        help=("The git branch to use. By default and when "
                              "'%(default)s' is specified branch-notes uses "
                              "the current git branch."))
    parser.add_argument(TOPLEVEL_OPTION, '-t', type=str,
                        help=("The project directory name under which the "
                              "notes file for the given branch is created."))
    parser.add_argument('--editor', type=str,
                        help=("The program used to create and open notes. If "
                              "set, branch-notes uses the given program. "
                              "Otherwise it tries to use the program "
                              "specified in the environment variable '%s', "
                              "or finally vi." % EDITOR_VARIABLE))
    return parser.parse_args()


def _determine_branch(options):
    """Determine the branch to be used from the given options."""
    # If CURRENT_BRANCH_OPTION is provided as the target branch we use the
    # current git branch.
    if options.branch == CURRENT_BRANCH_OPTION:
        branch = ""
        git_cmd = ['git', 'symbolic-ref', '--short', 'HEAD']
        try:
            branch = _get_output(git_cmd)
        except subprocess.CalledProcessError as error:
            print("Failed to determine git branch from current dir: %s" %
                  error)
            sys.exit(RESULT_ERROR)

        pattern = re.compile(r'^p4/(tasks|spfw)/')
        branch = pattern.sub('', branch)

    else:
        branch = options.branch

    return branch


def _get_output(cmd):
    """Return the output of the given subprocess call.
       Raises a CalledProcessError if anything goes wrong.
    """
    output = subprocess.check_output(cmd, encoding='UTF-8')
    # rstrip is necessary to remove the newline of the returned output.
    return output.rstrip()


def _find_notes(notes_dir, branch):
    """Return a list of toplevels for the given branch."""
    note_file = branch + ".txt"
    results = []
    for root, _, files in os.walk(notes_dir):
        if note_file in files:
            results.append(os.path.basename(root))
    return results


def _determine_toplevel(options, notes_dir, branch):
    """Determine and return the toplevel from the given options.

       The toplevel is determined in the following order:
       1) explicitly specified with TOPLEVEL_OPTION
       2) from the git toplevel of the current directory if no branch is
          specified on the commandline
       3) from the search for the notes file if a branch is given on the
          commandline
    """
    if options.toplevel:
        return options.toplevel

    elif options.branch == CURRENT_BRANCH_OPTION:
        git_cmd = ['git', 'rev-parse', '--show-toplevel']
        try:
            toplevel = _get_output(git_cmd)
        except subprocess.CalledProcessError as error:
            print("Failed to determine git toplevel from current dir: %s" %
                  error)
            print("Try specifying '%s'." % TOPLEVEL_OPTION)
            sys.exit(RESULT_ERROR)
        toplevel = os.path.basename(toplevel)

        return toplevel

    else:
        toplevels = _find_notes(notes_dir, branch)
        if len(toplevels) > 1:
            print("More than one note found for branch '%s'. Specify one of "
                  "the following toplevel directories: %s" %
                  (branch, ", ".join(toplevels)))
            sys.exit(RESULT_ERROR)

        elif len(toplevels) == 1:
            return toplevels[0]

        else:
            print("No notes file for branch '%s' found." % branch)
            sys.exit(RESULT_ERROR)


def _determine_notes_dir():
    """Determine and return the directory to store notes in."""
    try:
        # It is necessary to expand a tilde in the as otherwise the following
        # os.makedirs call creates a directory called '~'.
        notes_dir = os.path.expanduser(os.environ[NOTES_DIR_VARIABLE])
    except KeyError:
        print("Failed to determine notes directory. Set in environment "
              "variable '%s'." % NOTES_DIR_VARIABLE)
        sys.exit(RESULT_ERROR)
    return notes_dir


def _determine_editor(options):
    """Determine the editor to be used to open notes.

       Returns a list of the editor command. For example 'vim --noplugin' is
       returned as ['vim', '--noplugin'] so that it can be called with
       subprocess.
    """
    if options.editor:
        editor = options.editor
    else:
        try:
            editor = os.environ[EDITOR_VARIABLE]
        except KeyError:
            editor = "vi"
    return editor.split()


def _list_notes(options, notes_dir):
    """List all existing notes, or alternatively all notes under
       options.toplevel.
    """
    if options.toplevel:
        notes_dir = os.path.join(notes_dir, options.toplevel)

    for root, _, files in os.walk(notes_dir):
        if not files:
            continue

        print("%s: " % os.path.basename(root))
        for note in [note for note in files if not note.startswith('.')]:
            print("    %s" % os.path.splitext(note)[0])
        print("")


def main():
    """Main function for branch-notes."""
    options = _parse_options()

    notes_dir = _determine_notes_dir()
    if options.action == 'list':
        return _list_notes(options, notes_dir)

    branch = _determine_branch(options)
    toplevel = _determine_toplevel(options, notes_dir, branch)
    editor = _determine_editor(options)

    # Notes are placed in subdirectories according to their repository.
    notes_dir = os.path.join(notes_dir, toplevel)
    # Instead of checking whether a directory exists, we simply create it if
    # necessary and allow for it to exist already.
    os.makedirs(notes_dir, exist_ok=True)

    notes_file = os.path.join(notes_dir, branch + '.txt')

    editor_cmd = editor + [notes_file]
    try:
        subprocess.run(editor_cmd)
    except subprocess.CalledProcessError as error:
        print("Failed to run editor: %s" % error)
        return RESULT_ERROR


if __name__ == '__main__':
    sys.exit(main())
