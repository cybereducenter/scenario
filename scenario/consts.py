# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import json
import pkg_resources

from collections import OrderedDict

SCENARIO_JSON_SCHEMA_PATH = 'schema/scenario.json'
SCENARIO_JSON_SCHEMA = json.loads(
    pkg_resources.resource_stream('scenario',
                                  SCENARIO_JSON_SCHEMA_PATH).read().decode('utf-8'))

FEEDBACK_JSON_SCHEMA_PATH = 'schema/feedback.json'
FEEDBACK_JSON_SCHEMA = json.loads(
    pkg_resources.resource_stream('scenario',
                                  FEEDBACK_JSON_SCHEMA_PATH).read().decode('utf-8'))

VERBOSITY = OrderedDict(
    [('RETURN_CODE', 0),
     ('RESULT', 1),
     ('WARNING', 2),
     ('ERROR', 3),
     ('EXECUTION', 4),
     ('DEBUG', 5),
     ])

OUTPUT_FORMATS = ['json', 'text', 'html']

OUTPUT_FORMATS_DEFAULT = 'text'

OUTPUT_HTML_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'formats',
    'html')

# TODO from github
OUTPUT_HTML_RESOURCES_PATH_DEFALT = 'https://cdn.rawgit.com/shlomihod/scenario/v2.1.0/scenario/formats/html/'

with open(os.path.join(OUTPUT_HTML_PATH, 'index.html'), 'r', encoding='utf-8') as f:
    OUTPUT_HTML_PAGE = f.read()

RESULT_TEXT = {False: 'אי-הצלחה',
               True: 'הצלחה'
               }

QUOTE_TYPE_HE_TEXT = {'printing': 'הדפסה',
                      'output': 'פלט',
                      'negative_ouput': 'פלט שלילי'
                      'input': 'קלט'
                      }

# Delay before send/sendline in seconds
# In order to get currect `isalive` in Linux
# (not needed in macOS)
DELAY_BEFORE_SEND = 0.2

# https://people.cs.pitt.edu/~alanjawi/cs449/code/shell/UnixSignals.htm
SIGNALS = {
    1: ('SIGHUP', 'Hangup'),
    2: ('SIGINT', 'Interrupt'),
    3: ('SIGQUIT', 'Quit'),
    4: ('SIGILL', 'Illegal Instruction'),
    5: ('SIGTRAP', 'Trace/Breakpoint Trap'),
    6: ('SIGABRT', 'Abort'),
    7: ('SIGEMT', 'Emulation Trap'),
    8: ('SIGFPE', 'Arithmetic Exception'),
    9: ('SIGKILL', 'Killed'),
    10: ('SIGBUS', 'Bus Error'),
    11: ('SIGSEGV', 'Segmentation Fault'),
    12: ('SIGSYS', 'Bad System Call'),
    13: ('SIGPIPE', 'Broken Pipe'),
    14: ('SIGALRM', 'Alarm Clock'),
    15: ('SIGTERM', 'Terminated'),
    16: ('SIGUSR1', 'User Signal 1'),
    17: ('SIGUSR2', 'User Signal 2'),
    18: ('SIGCHLD', 'Child Status'),
    19: ('SIGPWR', 'Power Fail/Restart'),
    20: ('SIGWINCH', 'Window Size Change'),
    21: ('SIGURG', 'Urgent Socket Condition'),
    22: ('SIGPOLL', 'Socket I/O Possible'),
    23: ('SIGSTOP', 'Stopped (signal)'),
    24: ('SIGTSTP', 'Stopped (user)'),
    25: ('SIGCONT', 'Continued'),
    26: ('SIGTTIN', 'Stopped (tty input)'),
    27: ('SIGTTOU', 'Stopped (tty output)'),
    28: ('SIGVTALRM', 'Virtual Timer Expired'),
    29: ('SIGPROF', 'Profiling Timer Expired'),
    30: ('SIGXCPU', 'CPU time limit exceeded'),
    31: ('SIGXFSZ', 'File size limit exceeded'),
    32: ('SIGWAITING', 'All LWPs blocked'),
    33: ('SIGLWP', 'Virtual Interprocessor Interrupt for Threads Library'),
    34: ('SIGAIO', 'Asynchronous I/O')
}
