# Scenario

[![Build Status](https://semaphoreci.com/api/v1/cyber-org-il/scenario/branches/master/badge.svg)](https://semaphoreci.com/cyber-org-il/scenario)

Testing console applications I/O

## Install
`pip install git+https://github.com/shlomihod/scenario.git`

## Usage
```
usage: scenario [-h] [-v V] [-a A] [-u] [-d] [-s] [-t T] [-f {json,text,html}]
                [-p RESOURCES_PATH] [-i ID]
                executable_path scenario_path

Checking an IO scenario on execution.

positional arguments:
  executable_path       executable to be checked
  scenario_path         scenario file (or directory with -d flag)

optional arguments:
  -h, --help            show this help message and exit
  -v V                  set output verbosity
  -a A                  set extra arguments for executable
  -d, --directory       run on all scenario files (.json) in the directory
  -s, --forward-signal  forward signal from executable to scenario
  -t T                  set execution timeout in seconds
  -f {json,text,html}, --format {json,text,html}
                        output format to stdout
  -p RESOURCES_PATH, --resources-path RESOURCES_PATH
                        url to js/css resources for html output format
  -i ID, --id ID        div id for html output format
```

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
