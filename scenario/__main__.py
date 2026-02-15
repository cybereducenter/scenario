# -*- coding: utf-8 -*-

import sys
import os
import glob
import argparse
import traceback
import json

from scenario.runner import run_scenario
from scenario.parser import ParserError
from scenario.runner import run_unittest
from scenario.reporter import reporter_generate_html

from scenario.consts import VERBOSITY,      \
    OUTPUT_FORMATS, OUTPUT_FORMATS_DEFAULT, \
    OUTPUT_HTML_PAGE, OUTPUT_HTML_RESOURCES_PATH_DEFALT

from scenario.utils import build_feedback_text

__version__ = "1.2.3"

def main():

    result = False
    feedback_text = None

    parser = argparse.ArgumentParser(description='Checking an IO scenario on execution.')

    parser.add_argument('--version', action='version',version=f'%(prog)s {__version__}')

    parser.add_argument('executable_path', type=str,
                        help='executable to be checked')

    parser.add_argument('scenario_path', type=str,
                        help='test file (or directory with -d flag)')

    parser.add_argument('-u', '--unittest',
                        help='run a unittest on a python script',
                        action="store_true")
    
    parser.add_argument('-v', type=int,
                        help='set output verbosity')

    parser.add_argument('-a', type=str,
                        help='set extra arguments for executable')

    parser.add_argument('-d', '--directory',
                        help='run on all test files (.json) in the directory',
                        action="store_true")

    parser.add_argument('-s', '--forward-signal',
                        help='forward signal from executable to scenario',
                        action="store_true")

    parser.add_argument('-t', type=float,
                        help='set execution timeout in seconds')

    parser.add_argument('-f', '--format', default=OUTPUT_FORMATS_DEFAULT,
                        action='store', choices=OUTPUT_FORMATS, help='output format to stdout')

    parser.add_argument('-p', '--resources-path', action='store',
                        default=OUTPUT_HTML_RESOURCES_PATH_DEFALT,
                        help='url to js/css resources for html output format')

    parser.add_argument('-i', '--id', action='store', default=0,
                        help='div id for html output format')

    args = parser.parse_args()
    feedback_list = []

    try:
        if args.unittest:
            run_method = run_unittest
        else:
            run_method = run_scenario
        
        if not args.directory:
            feedback = run_method(args.executable_path,
                                    args.scenario_path,
                                    args.v,
                                    args.t,
                                    args.a)

            result = feedback['result']['bool']
            signal_ = feedback['signal_code']

            feedback_text = build_feedback_text(feedback)
            feedback_list.append(feedback)

        else:
            feedback_texts = []

            scenario_file_directory_path = os.path.join(args.scenario_path, '*.json')
            scenario_file_paths = glob.glob(scenario_file_directory_path)

            for scenario_file_path in scenario_file_paths:
                scenario_file_feedback = run_method(args.executable_path,
                                                      scenario_file_path,
                                                      args.v,
                                                      args.t,
                                                      args.a)

                feedback_list.append(scenario_file_feedback)
                feedback_texts.append(build_feedback_text(scenario_file_feedback))

            result = all([fb['result']['bool'] for fb in feedback_list])

            signals = [fb['signal_code'] for fb in feedback_list]
            signal_ = next((item for item in signals if item is not None), None)

            feedback_text = '\n\n\n'.join(feedback_texts)

    except ParserError as e:
        print(e.msg)
        sys.exit(2)

    except Exception as e:
        if args.v and args.v >= VERBOSITY['DEBUG']:
            traceback.print_exc()
        else:
            print('ERROR: {!s}'.format(e))
        sys.exit(-1)

    if args.format == 'json':
        print(json.dumps(feedback_list, indent=2, sort_keys=True))

    elif args.format == 'text':
        print(feedback_text)

    elif args.format == 'html':
        print(reporter_generate_html(feedback_list))
    
    if args.forward_signal and signal_ is not None:
        os.kill(os.getpid(), signal_)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
