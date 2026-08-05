# Scenario

[![Build Status](https://semaphoreci.com/api/v1/cyber-org-il/scenario/branches/master/badge.svg)](https://semaphoreci.com/cyber-org-il/scenario)

Testing console applications I/O

## Install
Clone this repository and install in editable mode (recommended, so the checkout stays in sync with any git updates):
```
git clone -b scenario_for_vpl https://github.com/cybereducenter/scenario.git
pip install -e scenario
```

## Usage
```
usage: scenario [-h] [--version] [-u] [-v V] [-a A] [-d] [-s] [-t T]
                [-f {json,text,html,vpl_html}] [-p RESOURCES_PATH] [-i ID]
                executable_path scenario_path

Checking an IO scenario on execution.

positional arguments:
  executable_path       executable to be checked
  scenario_path         test file (or directory with -d flag)

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -u, --unittest        run a unittest on a python script
  -v V                  set output verbosity
  -a A                  set extra arguments for executable
  -d, --directory       run on all test files (.json) in the directory
  -s, --forward-signal  forward signal from executable to scenario
  -t T                  set execution timeout in seconds
  -f {json,text,html,vpl_html}, --format {json,text,html,vpl_html}
                        output format to stdout
  -p RESOURCES_PATH, --resources-path RESOURCES_PATH
                        url to js/css resources for html output format
  -i ID, --id ID        div id for html output format
```

Whether `scenario_path` is run as a plain I/O scenario or as a unittest is decided purely by the `-u`/`--unittest` flag — pass it to run `run_unittest` (a unittest JSON checked against a Python script) instead of `run_scenario` (I/O checked against `executable_path`). It's not auto-detected from the file itself, so it must match how the test files were authored. This flag also drives which VPL report template `--format vpl_html` renders (`vpl_unittest` vs `vpl_scenario`).

## Exit Code
| Value | Meaning                   |
|-------|---------------------------|
|  0    | Success Scenario          |
|  1    | Failed Scenario           |
|  2    | Error in Scenario JSON    |
| -1    | Error in Scenario Program |

## Note
* `flow` should be `True`
* `strictness` should be `False`

## Known Issues (TODO update)
* Extra spaces in the beginning of a line with NONSTRICT mode won't be reported to user (yet the scenario will return success)
* Extra space in the end of a line with STRICT mode are ignored
* O Actor cann't be used for checking empty lines, even with STRICT mode
* Empty SNR file for only printing running doesn't work sometimes, only part of the printing is shown. Probably flush buffer issues.
