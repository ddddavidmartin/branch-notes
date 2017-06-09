Open and edit notes for the current or given git branch.

Work on a task branch and open notes for it simply by calling `branch-notes`.

By default a notes file is created as `NOTES_DIR/<toplevel>/<branch>.txt`, with
 - `NOTES_DIR` being read from the environment variable of the same name
 - `toplevel` being the name of the root directory of the git repository
 - `branch` being the name of the git branch


## Requirements

- Python 3


## Installation

```
cd /usr/local/bin
ln -s /path/to/repo/branch_notes.py branch-notes
```


## Usage

`branch-notes` to open the notes file for the current git repository and branch

`branch-notes --list` to list all existing notes

`branch-notes --help` to show all available options
