#! /usr/bin/env python
# encoding: utf-8

import os
import platform

top = '.'
out = 'build'

if platform.system() == 'Darwin' or platform.system() == 'Linux':
    default_prefix = '/usr/local/bin'


def options(ctx):
    ctx.add_option('--bash-compl-prefix', action='store', default=None,
                   help="Specify the directory for the bash autocompletion file.")


def configure(ctx):
    print("Setting installation directory to " + ctx.options.prefix + ".")
    if ctx.options.bash_compl_prefix:
        print("Setting Bash completion directory to " +
              ctx.options.bash_compl_prefix + ".")
        ctx.env.BASH_COMPL_PREFIX = ctx.options.bash_compl_prefix


def build(bld):
    source_path = os.path.join(bld.top_dir, 'branch_notes.py')
    dest_path = os.path.join(os.path.join('${PREFIX}', 'branch-notes'))
    # We simply link to the branch-notes source as this way changes in the
    # repo are directly applied.
    bld.symlink_as(dest_path, source_path)

    # We only install the bash-completion if a directory is specified, as this
    # is easier for now than trying to determine the correct directory.
    if bld.env.BASH_COMPL_PREFIX:
        print("Installing autocomp file as well")
        compl_file = 'branch_notes.bash-completion'
        compl_src = os.path.join(bld.top_dir, compl_file)
        compl_dst = os.path.join(bld.env.AUTOCOMP_PREFIX, compl_file)
        bld.symlink_as(compl_dst, compl_src)
