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

    compl_dir = None
    if ctx.options.bash_compl_prefix:
        compl_dir = ctx.options.bash_compl_prefix

    elif platform.system() == 'Darwin':
        compl_dir = '/usr/local/etc/bash_completion.d'

    elif platform.system() == 'Linux':
        compl_dir = '/etc/bash_completion.d'

    # We only use the auto-detected directory if it actually exists, as the
    # user may not have auto completion set up and we do not want to force it.
    # If the path is explicitly provided we will let waf create it.
    if compl_dir and os.path.isdir(compl_dir) or ctx.options.bash_compl_prefix:
        ctx.env.BASH_COMPL_PREFIX = compl_dir
        print("Setting Bash completion directory to " + compl_dir + ".")
    else:
        print("Not setting Bash completion directory. "
              "Specify with '--bash-compl-prefix=BASH_COMPL_PREFIX' if desired.")


def build(bld):
    source_path = os.path.join(bld.top_dir, 'branch_notes.py')
    dest_path = os.path.join(os.path.join('${PREFIX}', 'branch-notes'))
    # We simply link to the branch-notes source as this way changes in the
    # repo are directly applied.
    bld.symlink_as(dest_path, source_path)

    if bld.env.BASH_COMPL_PREFIX:
        compl_file = 'branch_notes.bash-completion'
        compl_src = os.path.join(bld.top_dir, compl_file)
        compl_dst = os.path.join(bld.env.BASH_COMPL_PREFIX, compl_file)
        bld.symlink_as(compl_dst, compl_src)
