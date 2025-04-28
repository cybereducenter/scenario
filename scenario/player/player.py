# -*- coding: utf-8 -*-

import re
import copy
import time

import pexpect
import jsonschema

from scenario.consts import FEEDBACK_JSON_SCHEMA, \
    DELAY_BEFORE_SEND

from scenario.player.feedback_exceptions import SholdNoOutputBeforeInput, \
    ShouldEOF,                \
    ShouldOutputBeforeEOF,    \
    ShouldInputBeforeEOF,     \
    ShouldOutput,             \
    NegativeOutput,           \
    MemoryFeedbackError

from scenario.utils import xstr,  \
    get_cleaned_before,  \
    get_cleaned_after,   \
    get_result_dict,     \
    get_quote_type_dict, \
    get_feedback_dict


def break_lines_log_quotes(feedback_log_quotes):
    new_feedback_log_quotes = []

    for quote in feedback_log_quotes:
        if quote['type']['en'] == 'printing' and '\r\n' in quote['value']:
            for line in quote['value'].splitlines(True):
                new_feedback_log_quotes.append({
                    'type': quote['type'],
                    'value': line
                })
        else:
            new_feedback_log_quotes.append(quote)

    return new_feedback_log_quotes


def play_scenario(scenario, executable_path,
                  executable_extra_args=None):

    feedback = copy.deepcopy(scenario)
    feedback['log'] = {'quotes': [], 'text': ''}
    feedback['feedback'] = {'type': None, 'text': None}

    executable_path_with_snr_args = executable_path

    if scenario['args']:
        executable_path_with_snr_args += ' ' + ' '.join(scenario['args'])

    if not executable_extra_args:
        p = pexpect.spawnu(
            executable_path_with_snr_args,
            timeout=scenario['timeout'], echo=False
        )

    else:
        executable_path_with_all_args = (executable_path_with_snr_args +
                                         ' ' + executable_extra_args)
        p = pexpect.spawnu(
            '/bin/bash', ['-c', executable_path_with_all_args],
            timeout=scenario['timeout'], echo=False
        )

    try:
        for index, quote in enumerate(scenario['dialogue']):

            # TODO: move list of types to constants file...
            if quote['type'] in ['input', 'output']:

                if quote['type'] == 'output':
                    patterns = []

                    # Right spaces cannot be seen in run example
                    quote_value = quote['value'].rstrip()

                    # if output is empty, then something need to be printed
                    if not quote_value:
                        escaped_quote_value = '.+\r\n'

                        pattern_quote_value = re.compile(escaped_quote_value)

                        patterns.append(pattern_quote_value)

                    else:
                        escaped_quote_value = re.escape(quote_value)
                        
                        pattern_quote_value = re.compile(escaped_quote_value)

                        patterns.append(pattern_quote_value)

                        if 'strictness' in quote:
                            strictness = quote['strictness']
                        else:
                            strictness = scenario['strictness']

                        assert isinstance(strictness, bool)

                        if not strictness:

                            pattern_cases = re.compile(escaped_quote_value,
                                                       re.IGNORECASE)
                            patterns.append(pattern_cases)

                            # expand only spaces
                            # spaces_pattern_string = re.escape(' '.join(quote_value.split())).replace('\ ', '\s+')

                            # expand between every two chars
                            spaces_pattern_string = ' '.join(list(quote_value.replace(' ', '').
                                                                  replace('\t', '')))
                            spaces_pattern_string = re.escape(spaces_pattern_string)
                            spaces_pattern_string = spaces_pattern_string.replace('\ ', '\s*')

                            pattern_spaces = re.compile(spaces_pattern_string)
                            patterns.append(pattern_spaces)

                            pattern_cases_spaces = re.compile(spaces_pattern_string, re.IGNORECASE)
                            patterns.append(pattern_cases_spaces)

                    try:
                        index = p.expect(patterns)
                    except pexpect.EOF:
                        raise ShouldOutputBeforeEOF(quote)
                    except pexpect.TIMEOUT:
                        raise ShouldOutput(quote)

                    # Negative output check
                    if (p.before is not None) and ('negative_output' in scenario):
                        for negative_output in scenario['negative_output']:
                            if negative_output in get_cleaned_before(p, scenario['strictness']):
                                quote['name'] = 'Negative output'
                                quote['value'] = negative_output
                                raise NegativeOutput(quote)
                    
                    # BEFORE the quote match
                    if not scenario['flow'] and get_cleaned_before(p, scenario['strictness']):
                        raise ShouldOutput(quote)

                    else:
                        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                                          'value': p.before,
                                                          })
                    # THE MATCH of the quote
                    assert p.after is not None
                    log_quote = {'type': get_quote_type_dict('output'),
                                 'name': quote['name'],
                                 'value': p.after,
                                 }
                    if 'strictness' in quote:
                        log_quote['strictness'] = quote['strictness']

                    feedback['log']['quotes'].append(log_quote)

                    # for flow False, no output should be
                    # AFTER the quote match UNTIL the END of the current LINE.
                    # And, for negative output, make sure the output does not come later.
                    if not scenario['flow'] or ('negative_output' in scenario):
                        p.expect(['\r\n', pexpect.TIMEOUT, pexpect.EOF])

                        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                                          'value': p.before + xstr(p.after)
                                                          })

                        if (p.before is not None) and ('negative_output' in scenario):
                            for negative_output in scenario['negative_output']:
                                if negative_output in get_cleaned_before(p, scenario['strictness']):
                                    quote['name'] = 'Negative output'
                                    quote['value'] = negative_output
                                    raise NegativeOutput(quote)

                        if get_cleaned_before(p, scenario['strictness']).strip(' ') and not scenario['flow']:
                            raise ShouldOutput(quote)

                    '''
                    if verbosity >= VERBOSITY['ERROR'] and index != 0:
                        if index == 1:
                            msg = 'Letter Cases'

                        if index == 2:
                            msg = 'Spaces'

                        if index == 3:
                            msg = 'Letter Cases & Spaces'

                        feedback['warnings'].append(
                            '[{:02d}] [WARNNING] {!s} are not precise'.format(n_line, msg) )
                    '''

                elif quote['type'] == 'input':

                    p.expect(['.+', pexpect.TIMEOUT, pexpect.EOF])

                    if not scenario['flow'] and get_cleaned_after(p, scenario['strictness']):
                        raise SholdNoOutputBeforeInput(quote)

                    time.sleep(DELAY_BEFORE_SEND)

                    if not p.isalive():
                        raise ShouldInputBeforeEOF(quote)

                    try:
                        p.sendline(quote['value'])
                    except OSError:
                        raise ShouldInputBeforeEOF(quote)

                    # relate to the p.expect inline 179 that catch everything
                    # it will run only if sendline was succefull,
                    # otherwise the priniting quote
                    # will be added in the relavent except blcok
                    # TODO: maybe refactor that, and remove the printing quote
                    # adding in the except block, and move this line stright
                    # after the p.expect call
                    feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                                      'value': p.before + xstr(p.after)
                                                      })

                    feedback['log']['quotes'].append({'type': get_quote_type_dict('input'),
                                                      'name': quote['name'],
                                                      'value': quote['value'] + '\r\n'
                                                      })

        if scenario['flow']:
            p.expect(['.+', pexpect.TIMEOUT, pexpect.EOF])

            feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                              'value': p.before + xstr(p.after)
                                              })

        try:
            p.expect(pexpect.EOF)

            if not scenario['flow'] and get_cleaned_before(p, scenario['strictness']):
                raise pexpect.TIMEOUT

    # REAL FEEDBACK EXCEPTIONS PART #

        except pexpect.TIMEOUT:
            raise ShouldEOF()

        # Negative output flip
        #if quote['type'] == 'negative_output':
        #    raise ShouldOutput(quote)

        feedback['result'] = get_result_dict(True)
        feedback['feedback'] = get_feedback_dict(None)

    except ShouldOutput as e:
        feedback['result'] = get_result_dict(False)

        # if scenario['flow']:
        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                          'value': p.before + xstr(p.after)
                                          })

        feedback['feedback'] = get_feedback_dict(e)
    
    except NegativeOutput as e:
        feedback['result'] = get_result_dict(False)
        feedback['feedback'] = get_feedback_dict(e)

    except SholdNoOutputBeforeInput as e:
        feedback['result'] = get_result_dict(False)

        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                          'value': p.before
                                          })

        feedback['last'] = True
        feedback['feedback'] = get_feedback_dict(e)

    except ShouldInputBeforeEOF as e:
        feedback['result'] = get_result_dict(False)

        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                          'value': p.before + xstr(p.after)
                                          })

        feedback['feedback'] = get_feedback_dict(e)

    except ShouldOutputBeforeEOF as e:
        feedback['result'] = get_result_dict(False)

        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                          'value': p.before + xstr(p.after)
                                          })

        feedback['last'] = True
        feedback['feedback'] = get_feedback_dict(e)

    except ShouldEOF as e:
        feedback['result'] = get_result_dict(False)

        feedback['log']['quotes'].append({'type': get_quote_type_dict('printing'),
                                          'value': p.before + xstr(p.after)
                                          })

        if not scenario['flow']:
            pass
            # feedback['feedback'].append('instead the last line')

        feedback['feedback'] = get_feedback_dict(e)

        '''
        if get_cleaned_before(p, scenario['strictness']):
            feedback.append('[{:02d}] {!r}'.format(
                n_line+1, get_cleaned_before(p, scenario['strictness']).split('\r\n')[0]))
        feedback.append('----> the program should have finished')
        if get_cleaned_before(p, scenario['strictness']):
            feedback.append('----> instead the last line')
        '''

    p.close()

    feedback['exit_code'] = p.exitstatus
    feedback['signal_code'] = p.signalstatus

    # http://www.tldp.org/LDP/abs/html/exitcodes.html
    if (feedback['exit_code'] is not None and
            129 <= feedback['exit_code'] <= 162):
        feedback['signal_code'] = feedback['exit_code'] - 128
        feedback['exit_code'] = None

    if (feedback['signal_code'] is not None and
            feedback['signal_code'] == 0):
        feedback['signal_code'] = None

    # WHY?
    if feedback['signal_code'] == 1:
        feedback['signal_code'] = None

    if feedback['signal_code'] is not None:
        feedback['result'] = get_result_dict(False)
        feedback['feedback'] = get_feedback_dict(MemoryFeedbackError())

    feedback['log']['quotes'] = break_lines_log_quotes(
        feedback['log']['quotes'])

    # Generate feedback LOG text
    for quote in feedback['log']['quotes']:
        if quote['type']['en'] == 'output' or quote['type']['en'] == 'negative_output':
            feedback['log']['text'] += '<<'

        feedback['log']['text'] += quote['value']

        if quote['type']['en'] == 'output':
            feedback['log']['text'] += '>>'

    jsonschema.validate(feedback, FEEDBACK_JSON_SCHEMA)

    return feedback
