import unittest
import pprint

import jsonschema

from scenario.player import play_scenario
from scenario.tests.consts import EXECUTABLE, DIALOUGE_PIECES
from scenario.consts import SCENARIO_JSON_SCHEMA, SCENARIO_LOG_MAX_TOTAL_CHARS


class PlayerTest(unittest.TestCase):

    def _generate_scenario(self, name, args, dialogue, strictness=False):
        scenario = {
            'id': name,
            'name': name,
            'description': name,
            'flow': True,
            'strictness': strictness,
            'timeout': 1,
            'verbosity': 4,
            'args': args,
            'dialogue': dialogue
        }

        return scenario

    def _run_test(self, result_bool, feedback_type, args, dialogue, **kwargs):
        name = '='.join([str(result_bool),
                         str(feedback_type),
                         '+'.join(args)])

        scenario = self._generate_scenario(name, args, dialogue, **kwargs)

        jsonschema.validate(scenario, SCENARIO_JSON_SCHEMA)

        feedback = play_scenario(scenario, EXECUTABLE)

        print('args:')
        pprint.pprint(args)
        print

        print('dialogue:')
        pprint.pprint(dialogue)
        print

        pprint.pprint(feedback['log'])

        self.assertEqual(feedback['result']['bool'], result_bool)
        self.assertEqual(feedback['feedback']['type'], feedback_type)

        return feedback


class ResultTrueTests(PlayerTest):

    def test_all_print(self):
        '''
        Working: Empty Scenario
        Empty `dialogue` with only print executable
        '''

        dialogue = []

        args = ['print']

        self._run_test(True, None, args, dialogue)

    def test_all_output(self):
        '''
        Working: All Output
        `dialogue` contains all output of executable
        '''

        dialogue = DIALOUGE_PIECES['output_all']

        args = ['print']

        self._run_test(True, None, args, dialogue)

    def test_one_output(self):
        '''
        Working: One Output
        `dialogue` contains one output of executable
        '''

        dialogue = [DIALOUGE_PIECES['output4']]

        args = ['print']

        self._run_test(True, None, args, dialogue)

    def test_one_output_input_output(self):
        '''
        Working: One Output -> Input -> Output (flow=True)
        `dialogue` contains one output line of executable
        and then input and output
        '''

        dialogue = [DIALOUGE_PIECES['output4'],
                    DIALOUGE_PIECES['input_comment'],
                    DIALOUGE_PIECES['output_comment']]

        args = ['print', 'input', 'output']

        self._run_test(True, None, args, dialogue)

    def test_input_one_output_output(self):
        '''
        Working: Input -> One Output -> Output (flow=True)
        `dialogue` contains one output line of executable
        but before input and after output
        '''

        dialogue = [DIALOUGE_PIECES['input_comment'],
                    DIALOUGE_PIECES['output4'],
                    DIALOUGE_PIECES['output_comment']]

        args = ['input', 'print', 'output']

        self._run_test(True, None, args, dialogue)


class StrictnnessTests(PlayerTest):

    def _run_strictness_test(self, result_bool, feedback_type,
                             sglobal, slocal=None):
        '''
        Helper method: One Output Upper (strictness: sglobal & slocal)
        `dialogue` contains upper case one output of executable
        '''

        quote = DIALOUGE_PIECES['output4_upper'].copy()

        if slocal is not None:
            quote['strictness'] = slocal

        dialogue = [quote]

        args = ['print']

        self._run_test(result_bool, feedback_type, args, dialogue,
                       strictness=sglobal)

    def test_one_output_upper_strictness_global_false(self):
        '''
        Working: One Output Upper (strictness: global=False)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(True, None,
                                  sglobal=False)

    def test_one_output_upper_strictness_global_true(self):
        '''
        Not Working: One Output Upper (strictness: global=True)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(False, 'ShouldOutputBeforeEOF',
                                  sglobal=True)

    def test_one_output_upper_strictness_local_false_global_false(self):
        '''
        Working: One Output Upper (strictness: local=False, global=False)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(True, None,
                                  sglobal=False,
                                  slocal=False)

    def test_one_output_upper_strictness_local_true_global_false(self):
        '''
        Not Working: One Output Upper (strictness: local=True, global=False)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(False, 'ShouldOutputBeforeEOF',
                                  sglobal=False,
                                  slocal=True)

    def test_one_output_upper_strictness_local_false_global_true(self):
        '''
        Working: One Output Upper (strictness: local=False, global=True)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(True, None,
                                  sglobal=True,
                                  slocal=False)

    def test_one_output_upper_strictness_local_true_global_true(self):
        '''
        Not Working: One Output Upper (strictness: local=True, global=True)
        `dialogue` contains upper case one output of executable
        '''

        self._run_strictness_test(False, 'ShouldOutputBeforeEOF',
                                  sglobal=True,
                                  slocal=True)


class ResultFalseTests(PlayerTest):
    def test_ScenarioTimeout_waiting_for_output(self):
        '''
        Feedback Error: Scenario timeout while waiting for output
        '''

        dialogue = [DIALOUGE_PIECES['output_poet']]

        args = ['print', 'input']

        self._run_test(False, 'ScenarioTimeout', args, dialogue)

    def test_ScenarioTimeout_waiting_for_eof(self):
        '''
        Feedback Error: Scenario timeout while waiting for EOF
        '''

        dialogue = [DIALOUGE_PIECES['output4']]

        args = ['print', 'input']

        self._run_test(False, 'ScenarioTimeout', args, dialogue)

    def test_ShouldOutputBeforeEOF(self):
        '''
        Feedback Error: Shpuld Output Before EOF
        '''

        dialogue = [DIALOUGE_PIECES['output4'],
                    DIALOUGE_PIECES['output_poet']]

        args = ['print']

        self._run_test(False, 'ShouldOutputBeforeEOF', args, dialogue)

    def test_SholdNoOutputBeforeInput(self):
        '''
        Feedback Error: Should No Output Before Input (flow=False)
        '''

        raise unittest.SkipTest

    def test_ShouldInputBeforeEOF(self):
        '''
        Feedback Error: Should Input Before EOF
        '''

        dialogue = [DIALOUGE_PIECES['output4'],
                    DIALOUGE_PIECES['input_comment']]

        args = ['print']

        self._run_test(False, 'ShouldInputBeforeEOF', args, dialogue)

    def test_MemoryFeedbackError(self):
        pass


class ScenarioLogCapTests(PlayerTest):

    def test_timeout_output_is_capped(self):
        scenario = self._generate_scenario(
            'scenario-log-cap',
            ['ADD', '2', '3', '5', '7', '11', '13'],
            [{
                'type': 'output',
                'name': 'result',
                'value': '41',
            }],
        )

        executable = '/home/ubuntu/scenario/scenario/tests/infinite_loop/program'
        feedback = play_scenario(scenario, executable)

        self.assertEqual(feedback['result']['bool'], False)
        self.assertEqual(feedback['feedback']['type'], 'ScenarioTimeout')
        self.assertIn('output shortened', feedback['log']['text'])
        self.assertLessEqual(len(feedback['log']['text']), SCENARIO_LOG_MAX_TOTAL_CHARS)



class MemoryTests(PlayerTest):
    def test_MemoryFeedback(self):
        '''
        Feedback Error: MemoryFeedback
        '''

        dialogue = [DIALOUGE_PIECES['output_poet'],
                    DIALOUGE_PIECES['input_comment']]

        args = ['print', 'crash', 'input']

        self._run_test(False, 'MemoryFeedbackError', args, dialogue)


class LogTests(PlayerTest):
    def test_log_break_lines(self):
        '''
        Log: Break Lines
        The \\r\\n should be added only for the last log quote in the line
        '''

        dialogue = [DIALOUGE_PIECES['output4_middle']]

        args = ['print']

        feedback = self._run_test(True, None, args, dialogue)

        self.assertEqual(feedback['log']['quotes'][4]['value'],
                         DIALOUGE_PIECES['output4_prefix']['value'])

        self.assertEqual(feedback['log']['quotes'][5]['value'],
                         DIALOUGE_PIECES['output4_middle']['value'])

        self.assertEqual(feedback['log']['quotes'][6]['value'],
                         DIALOUGE_PIECES['output4_suffix']['value'] + '\r\n')
