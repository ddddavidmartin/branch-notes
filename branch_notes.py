#! /usr/bin/env python3

"""Open and edit notes for the given git branch."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import shutil
import sys


# Environment variable name that is used to specify the notes directory.
NOTES_DIR_VARIABLE = 'NOTES_DIR'

# The name for the notes directory if the NOTES_DIR_VARIABLE is not set.
DEFAULT_NOTES_DIR_NAME = 'branch-notes'

# Generic environment variable name that is used to specify the notes editor.
EDITOR_VARIABLE = 'NOTES_EDITOR'

RESULT_SUCCESS = 0
RESULT_ERROR = 1

BRANCH_OPTION = 'branch'
TOPLEVEL_OPTION = '--toplevel'
CURRENT_BRANCH_OPTION = '-'

# The name of the directory used for archiving notes.
# It created placed as a subdirectory of NOTES_DIR_VARIABLE.
ARCHIVE_DIR = 'ARCHIVE'

# The file extension used for notes files.
NOTES_EXT = '.txt'

ACTIONS = ['open', 'list', 'archive']


class BranchNotesError(Exception):
    """Generic error class for expected errors when running branch-notes"""


def _parse_options():
    """Parse the provided command line parameters."""
    descr = ("Open and edit notes for the given branch. "
             "By default a notes file is created under "
             "'NOTES_DIR/<toplevel>/<branch>%s'. NOTES_DIR is read from the "
             "environment variable '%s' and defaults to '%s/%s'." %
             (NOTES_EXT, NOTES_DIR_VARIABLE, Path.home(),
              DEFAULT_NOTES_DIR_NAME))
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('action', choices=ACTIONS,
                        help=("open - open given note; "
                              "list - list existing notes; "
                              "archive - archive given note."))
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


def _walk_notes_dir(notes_dir):
    """Walk the given notes_dir whilst skipping the ARCHIVE."""
    for root, dirs, files in os.walk(notes_dir, topdown=True):
        dirs[:] = [d for d in dirs if d != ARCHIVE_DIR]
        yield (root, files)


def _find_notes(notes_dir, branch):
    """Return a list of toplevels for the given branch."""
    note_file = branch + NOTES_EXT
    results = []
    for root, files in _walk_notes_dir(notes_dir):
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
       4) from the current git toplevel if no existing notes file exists for
          the branch
    """
    def current_toplevel():
        """Return the toplevel of the current git repo."""
        git_cmd = ['git', 'rev-parse', '--show-toplevel']
        try:
            toplevel = _get_output(git_cmd)
        except subprocess.CalledProcessError as error:
            print("Failed to determine git toplevel from current dir: %s" %
                  error)
            print("Try specifying '%s'." % TOPLEVEL_OPTION)
            sys.exit(RESULT_ERROR)
        return os.path.basename(toplevel)

    if options.toplevel:
        return options.toplevel

    if options.branch == CURRENT_BRANCH_OPTION:
        return current_toplevel()

    toplevels = _find_notes(notes_dir, branch)
    if len(toplevels) > 1:
        print("More than one note found for branch '%s'. Specify one of "
              "the following toplevel directories: %s" %
              (branch, ", ".join(toplevels)))
        sys.exit(RESULT_ERROR)

    elif len(toplevels) == 1:
        return toplevels[0]

    else:
        return current_toplevel()


def _determine_notes_dir():
    """Determine and return the directory to store notes in."""
    try:
        # It is necessary to expand a tilde in the as otherwise the following
        # os.makedirs call creates a directory called '~'.
        notes_dir = os.path.expanduser(os.environ[NOTES_DIR_VARIABLE])
    except KeyError:
        notes_dir = os.path.join(str(Path.home()), DEFAULT_NOTES_DIR_NAME)
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

    for root, files in _walk_notes_dir(notes_dir):
        notes = [note for note in files if not note.startswith('.') and
                 note.endswith(NOTES_EXT)]

        if not notes:
            continue

        print("%s: " % os.path.basename(root))
        for note in notes:
            print("    %s" % os.path.splitext(note)[0])
        print("")


def _makedir(directory):
    # Instead of checking whether a directory exists, we simply create it if
    # necessary and allow for it to exist already.
    os.makedirs(directory, exist_ok=True)


def _open_note(notes_dir, notes_file, editor):
    """Open or create the given notes file with the given editor."""
    _makedir(notes_dir)

    editor_cmd = editor + [notes_file]
    try:
        subprocess.run(editor_cmd)
    except subprocess.CalledProcessError as error:
        raise BranchNotesError(f"Failed to run editor: {error}")


def _archive_note(toplevel, notes_file):
    """Archive the given notes file."""
    if not os.path.isfile(notes_file):
        raise BranchNotesError(f"Note '{notes_file}' does not exist.")

    archive_dir = os.path.join(_determine_notes_dir(), ARCHIVE_DIR, toplevel)
    _makedir(archive_dir)

    shutil.move(notes_file,
                os.path.join(archive_dir, os.path.basename(notes_file)))
    print("Done.")


def main():
    """Main function for branch-notes."""
    options = _parse_options()

    notes_dir = _determine_notes_dir()
    if options.action == 'list':
        _list_notes(options, notes_dir)
        return

    branch = _determine_branch(options)
    toplevel = _determine_toplevel(options, notes_dir, branch)
    editor = _determine_editor(options)

    # Notes are placed in subdirectories according to their repository.
    notes_dir = os.path.join(notes_dir, toplevel)
    notes_file = os.path.join(notes_dir, branch + NOTES_EXT)

    if options.action == 'open':
        _open_note(notes_dir, notes_file, editor)
    elif options.action == 'archive':
        _archive_note(toplevel, notes_file)


if __name__ == '__main__':
    try:
        main()
    except BranchNotesError as error:
        print(f"Error: {error}")
        sys.exit(RESULT_ERROR)
    sys.exit(RESULT_SUCCESS)
