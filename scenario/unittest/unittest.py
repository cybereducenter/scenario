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
import multiprocessing
from contextlib import contextmanager

from scenario.consts import UNITTEST_TIMEOUT_DEFAULT

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
    def _build_results_text(self, feedback_dict):
        lines = ["UNIT TEST RESULTS", "=" * 17]
        
        # Sort by key (assuming keys are string representations of integers
        for i in sorted(feedback_dict, key=lambda x: int(x)):
            fb = feedback_dict[i]
            
            # Extract data
            method = fb.get('method_name', 'Unknown Method')
            args = fb.get('arguments_sent', '')
            success = fb.get('result', {}).get('bool', False)
            status = "PASS" if success else "FAIL"
            
            # Build the test header line
            lines.append(f"\n[{status}] {method}({args})")
            
            # Add details only if they exist or are relevant
            lines.append(f"  Expected: {fb.get('expected', 'N/A')}")
            lines.append(f"  Actual:   {fb.get('returned_value', 'N/A')}")
            
            # Only show stdout if there is actual content to see
            stdout = fb.get('actual_stdout')
            if stdout:
                lines.append(f"  Stdout:   {stdout}")
            
        return "\n".join(lines)

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

    def _check_args(self, method_signature, method_name, log_buffer, namespace):
        try:
            left = method_signature.find('(') + 1
            right = method_signature.find(')')
            expected_args = method_signature[left:right].replace(' ', '').split(',')
            inspected_args = inspect.getfullargspec(namespace[method_name]).args
            return inspected_args == expected_args
        except Exception:
            return False

    def _test_signature(self, json_data, log_buffer, namespace):
        method_name = json_data.get('method_name', 'solution')
        method_signature = json_data.get('method_signature', 'solution')
        if method_name not in namespace:
            return False, FUNC_NAME_FEEDBACK_MSG.format(method_name)
        if method_signature != 'solution' and not self._check_args(method_signature, method_name, log_buffer, namespace):
            return False, SIGNATURE_FEEDBACK_MSG.format(method_signature)
        return True, ""

    def _run_single_test(self, json_data, json_output, namespace, external_index=0):
        ext_str = str(external_index)
        test = json_data['test'][0]
        method_name = json_data.get('method_name', 'solution')

        if method_name not in namespace:
            res = self._create_result(json_data, False, 'Failure')
            res['feedback'] = {'text': f'Function "{method_name}" not found.', 'type': 'NameError'}
            json_output[ext_str] = res
            return json_output, False

        student_method = namespace[method_name]
        return self._test_the_method(json_data, test, student_method, json_output, method_name, ext_str)

def _run_unittest_worker(unittest_data, code, result_queue):
    tester = StandalonePythonUnitTest()
    log_buffer = []
    namespace = {"__builtins__": __builtins__, "__name__": "__main__"}

    try:
        exec(code, namespace)
    except Exception as e:
        result_queue.put({
            "status": "feedback",
            "feedback": {"type": "ImportError", "text": f"{CODE_ERROR_FEEDBACK_MSG}: {repr(e)}"},
        })
        return

    sig_ok, sig_msg = tester._test_signature(unittest_data, log_buffer, namespace)
    if not sig_ok:
        result_queue.put({
            "status": "feedback",
            "feedback": {"type": "SignatureError", "text": sig_msg},
        })
        return

    try:
        json_output, success = tester._run_single_test(unittest_data, {}, namespace)
        result_queue.put({
            "status": "success",
            "json_output": json_output,
            "success": success,
        })
    except Exception as e:
        result_queue.put({
            "status": "feedback",
            "feedback": {"type": "UnexpectedError", "text": str(e)},
        })


def play_unittest(unittest, student_file_path, timeout=None):
    feedback = copy.deepcopy(unittest)
    feedback["result"] = {"bool": False}
    feedback["signal_code"] = None
    feedback["exit_code"] = 1
    feedback["log"] = {"quotes": [], "text": ""}
    feedback["feedback"] = {"type": "UnknownUnittestError", "text": None}

    if not os.path.exists(student_file_path):
        feedback['feedback']['type'] = "FileError"
        feedback['feedback']['text'] = "Student file not found."
        return feedback

    tester = StandalonePythonUnitTest()
    code_path = LANGUAGE_DATA['python']['code_path']
    json_output = {}
    effective_timeout = timeout
    if effective_timeout is None:
        effective_timeout = unittest.get('timeout', UNITTEST_TIMEOUT_DEFAULT)
    
    try:
        with open(student_file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        with open(code_path, 'w', encoding='utf-8') as cf:
            cf.write(code)

        # Syntax Check
        res = subprocess.run(
            [sys.executable, '-m', 'py_compile', code_path],
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
        if res.returncode != 0:
            feedback['feedback'] = {"type": "SyntaxError", "text": res.stdout or res.stderr}
            return feedback

        result_queue = multiprocessing.Queue()
        worker = multiprocessing.Process(
            target=_run_unittest_worker,
            args=(unittest, code, result_queue),
        )
        worker.start()
        worker.join(effective_timeout)

        if worker.is_alive():
            worker.terminate()
            worker.join()
            feedback['feedback'] = {
                "type": "TimeoutError",
                "text": f"Unittest execution exceeded {effective_timeout} seconds. The code may be stuck in an infinite loop.",
            }
            return feedback

        if worker.exitcode not in (0, None) and result_queue.empty():
            feedback['feedback'] = {
                "type": "UnexpectedError",
                "text": "The unittest worker process exited unexpectedly.",
            }
            return feedback

        worker_result = result_queue.get() if not result_queue.empty() else {
            "status": "feedback",
            "feedback": {"type": "UnexpectedError", "text": "No result returned from unittest worker."},
        }

        if worker_result['status'] == 'feedback':
            feedback['feedback'] = worker_result['feedback']
            return feedback

        json_output = worker_result['json_output']
        success = worker_result['success']
        feedback['result']['bool'] = bool(success)

        # Formatting values for the text field
        for item in json_output.values():
            if 'returned_value' in item: item['returned_value'] = repr(item['returned_value'])
            if 'expected' in item: item['expected'] = repr(item['expected'])

        n_snr = len(json_output)
        n_success = sum(1 for item in json_output.values() if item.get('result', {}).get('bool'))
        feedback['exit_code'] = 0 if feedback['result']['bool'] else 1
        feedback['log']['text'] = tester._build_results_text(json_output)
        
        if feedback['result']['bool']:
            feedback['feedback'] = {"type": None, "text": None}
        else:
            feedback['feedback'] = {"type": "TestFailure", "text": f"Passed {n_success}/{n_snr} tests."}

    except subprocess.TimeoutExpired:
        feedback['feedback'] = {
            "type": "TimeoutError",
            "text": f"Unittest syntax check exceeded {effective_timeout} seconds.",
        }
    except Exception as e:
        feedback['feedback'] = {"type": "UnexpectedError", "text": str(e)}
    finally:
        if os.path.exists(code_path): os.remove(code_path)

    return feedback
