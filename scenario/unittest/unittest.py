import logging
import os
import io
import subprocess
import json
import copy
import sys
import pathlib
import unittest
import inspect
from contextlib import contextmanager

# --- Configuration & Messages ---
SIGNATURE_FEEDBACK_MSG = 'Function signature in code does not match required.\nExpected: {}\n'
FUNC_NAME_FEEDBACK_MSG = 'Function name does not match required.\nExpected: {}\n'
FUNC_ERROR_FEEDBACK_MSG = 'An error occurred while running the function. Debug the code and resubmit.'
CODE_ERROR_FEEDBACK_MSG = 'An error occurred during code execution/import.'

LANGUAGE_DATA = {
    'python': {
        'code_path': 'temp_student_code.py',
    }
}

TEST_TYPES = {
    'equal': {'method_name': 'assertEqual'},
    'not_equal': {'method_name': 'assertNotEqual'},
    'count_equal': {'method_name': 'assertCountEqual'}
}

test_case = unittest.TestCase()

class PrintOutException(Exception):
    pass

class StandalonePythonUnitTest:
    def _build_results_table_html(self, feedback_dict):
        has_print_tests = any(
            fb.get('actual_stdout') or fb.get('expected_stdout') 
            for fb in feedback_dict.values()
        )
        
        html = ['<div class="python-unittest-results">', '<table class="unittest-table">']
        html.append('<thead><tr>')
        html.append('<th class="unittest-th">Actual</th>')
        html.append('<th class="unittest-th">Expected</th>')
        if has_print_tests:
            html.append('<th class="unittest-th">Print Output</th>')
        html.append('<th class="unittest-th">Test Details</th>')
        html.append('<th class="unittest-th unittest-status">Status</th>')
        html.append('</tr></thead><tbody>')
        
        for i in sorted(feedback_dict, key=lambda x: int(x)):
            fb = feedback_dict[i]
            actual = fb.get('returned_value', '')
            expected = fb.get('expected', '')
            method = fb.get('method_name', '')
            args = fb.get('arguments_sent', '')
            success = fb.get('result', {}).get('bool', False)
            actual_stdout = fb.get('actual_stdout', '')
            
            details = f"<strong>{method}</strong>(<code>{args}</code>)"
            status_icon = '✔' if success else '❌'
            color = 'green' if success else 'red'
            
            html.append('<tr>')
            html.append(f'<td class="unittest-td">{actual or "No Return"}</td>')
            html.append(f'<td class="unittest-td">{expected or "No Expected"}</td>')
            if has_print_tests:
                html.append(f'<td class="unittest-td">{actual_stdout or "No Output"}</td>')
            html.append(f'<td class="unittest-td">{details}</td>')
            html.append(f'<td class="unittest-td" style="color: {color}">{status_icon}</td>')
            html.append('</tr>')
        
        html.append('</tbody></table></div>')
        css = '<style>.unittest-table { border: 1px solid #ccc; width: 100%; border-collapse: collapse; } .unittest-th, .unittest-td { border: 1px solid #ccc; padding: 8px; text-align: left; }</style>'
        return css + '\n'.join(html)

    def _create_result(self, json_data, result_bool, result_text):
        json_data['result'] = {'bool': result_bool, 'text': result_text}
        return json_data

    @contextmanager
    def _stdout_redirector(self, stream):
        old_stdout = sys.stdout
        sys.stdout = stream
        try:
            yield
        finally:
            sys.stdout = old_stdout

    def _test_the_method(self, json_data, test, student_method_sent, json_output, method_name, external_index_string):
        success = False
        returned_value = None
        captured_output = None
        
        if TEST_TYPES.get(test['type']):
            test_method_name = TEST_TYPES[test['type']]['method_name']
            test_method = getattr(test_case, test_method_name)
            expected_value = test['expected']
            args = copy.deepcopy(test['args'])

            try:
                f = io.StringIO()
                with self._stdout_redirector(f):
                    returned_value = student_method_sent(*args)
                
                captured_output = f.getvalue()
                if test.get('expected_stdout') and test['expected_stdout'] != [line.strip() for line in captured_output.strip().splitlines()]:
                    raise PrintOutException

                test_method(returned_value, expected_value)
                result = self._create_result(json_data, True, 'Success')
                success = True

            except Exception as e:
                result = self._create_result(json_data, False, 'Failure')
                err_type = 'PrintMismatch' if isinstance(e, PrintOutException) else 'AssertionError'
                result['feedback'] = {'text': str(e) or 'Test Failed', 'type': err_type, 'technical_error': repr(e)}
            
            result.update({
                'actual_stdout': captured_output,
                'expected': expected_value,
                'method_name': method_name,
                'returned_value': returned_value,
                'arguments_sent': test['args']
            })
            json_output[external_index_string] = result
        return json_output, success

    def _check_args(self, method_signature, method_name, log_buffer):
        try:
            left = method_signature.find('(') + 1
            right = method_signature.find(')')
            expected_args = method_signature[left:right].replace(' ', '').split(',')
            inspected_args = inspect.getfullargspec(globals()[method_name]).args
            return inspected_args == expected_args
        except Exception:
            return False

    def _test_signature(self, json_data, log_buffer):
        method_name = json_data.get('method_name', 'solution')
        method_signature = json_data.get('method_signature', 'solution')
        if method_name not in globals():
            return False, FUNC_NAME_FEEDBACK_MSG.format(method_name)
        if method_signature != 'solution' and not self._check_args(method_signature, method_name, log_buffer):
            return False, SIGNATURE_FEEDBACK_MSG.format(method_signature)
        return True, ""

    def _run_single_test(self, json_data, json_output, external_index):
        ext_str = str(external_index)
        test = json_data['test'][0]
        method_name = json_data.get('method_name', 'solution')

        if method_name not in globals():
            res = self._create_result(json_data, False, 'Failure')
            res['feedback'] = {'text': f'Function "{method_name}" not found.', 'type': 'NameError'}
            json_output[ext_str] = res
            return json_output, False

        student_method = globals()[method_name]
        return self._test_the_method(json_data, test, student_method, json_output, method_name, ext_str)

def run_unittest(student_file_path, test_path, verbosity=None, timeout=None, extra_args=None):
    feedback = {
        "id": "unitest_dummy", #TODO: make this a real id
        "result": {"bool": False},
        "signal_code": None,
        "exit_code": 1,
        "log": {"quotes": [], "text": ""},
        "feedback": {"type": "UnknownUnittestError", "text": None}
    }
    log_buffer = []

    if not os.path.exists(student_file_path):
        feedback['feedback']['type'] = "FileError"
        feedback['feedback']['text'] = "Student file not found."
        return feedback

    test_json_files = []
    if os.path.isdir(test_path):
        test_json_files = sorted(pathlib.Path(test_path).glob('*.json'))
    elif os.path.isfile(test_path):
        test_json_files = [pathlib.Path(test_path)]

    tester = StandalonePythonUnitTest()
    code_path = LANGUAGE_DATA['python']['code_path']
    json_output, n_snr, n_success = {}, 0, 0
    
    try:
        with open(student_file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        with open(code_path, 'w', encoding='utf-8') as cf:
            cf.write(code)

        # Syntax Check
        res = subprocess.run([sys.executable, '-m', 'py_compile', code_path], capture_output=True, text=True)
        if res.returncode != 0:
            feedback['feedback'] = {"type": "SyntaxError", "text": res.stdout or res.stderr}
            return feedback

        # Exec
        try:
            exec(code, globals())
        except Exception as e:
            feedback['feedback'] = {"type": "ImportError", "text": f"{CODE_ERROR_FEEDBACK_MSG}: {repr(e)}"}
            return feedback

        for idx, json_path in enumerate(test_json_files):
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if idx == 0:
                sig_ok, sig_msg = tester._test_signature(json_data, log_buffer)
                if not sig_ok:
                    feedback['feedback'] = {"type": "SignatureError", "text": sig_msg}
                    return feedback

            n_snr += 1
            json_output, success = tester._run_single_test(json_data, json_output, idx)
            if success: n_success += 1

        # Formatting values for the HTML table
        for item in json_output.values():
            if 'returned_value' in item: item['returned_value'] = repr(item['returned_value'])
            if 'expected' in item: item['expected'] = repr(item['expected'])

        feedback['result']['bool'] = (n_success == n_snr and n_snr > 0)
        feedback['exit_code'] = 0 if feedback['result']['bool'] else 1
        feedback['log']['text'] = tester._build_results_table_html(json_output)
        
        if not feedback['result']['bool']:
            feedback['feedback'] = {"type": "TestFailure", "text": f"Passed {n_success}/{n_snr} tests."}

    except Exception as e:
        feedback['feedback'] = {"type": "UnexpectedError", "text": str(e)}
    finally:
        if os.path.exists(code_path): os.remove(code_path)

    return feedback