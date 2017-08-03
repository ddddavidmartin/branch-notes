#! /usr/bin/env python
# encoding: utf-8

import os

top = '.'
out = 'build'


def configure(ctx):
    print("Installation directory is set to " + ctx.options.prefix + ".")


def build(bld):
    source_path = os.path.join(bld.top_dir, 'branch_notes.py')
    dest_path = os.path.join(os.path.join('${PREFIX}', 'branch-notes'))
    # We simply link to the branch-notes source as this way changes in the
    # repo are directly applied.
    bld.symlink_as(dest_path, source_path)
