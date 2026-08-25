import os
import tempfile
import unittest as pyunit

import jsonschema

from scenario.consts import UNITTEST_JSON_SCHEMA
from scenario.unittest import play_unittest


STUDENT_CODE_WRITES_FILE = '''
def write_output(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True
'''

STUDENT_CODE_NO_FILE = '''
def write_output(path, content):
    return True
'''

STUDENT_CODE_WRONG_RETURN = '''
def write_output(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return False
'''


class FileCompareTest(pyunit.TestCase):
    def _spec(self, args, expected, file_compare):
        return {
            "id": "01-test",
            "name": "writes output",
            "description": "writes the expected content to a file",
            "method_name": "write_output",
            "method_signature": "write_output(path, content)",
            "test": [
                {"type": "equal", "args": args, "expected": expected,
                 "error": "did not return the expected value"}
            ],
            "file_compare": file_compare,
        }

    def _write_student_file(self, workdir, code):
        student_path = os.path.join(workdir, "student.py")
        with open(student_path, "w", encoding="utf-8") as f:
            f.write(code)
        return student_path

    def _run(self, workdir, code, args, expected, file_compare):
        student_path = self._write_student_file(workdir, code)
        spec = self._spec(args, expected, file_compare)
        cwd = os.getcwd()
        os.chdir(workdir)
        try:
            return play_unittest(spec, student_path)
        finally:
            os.chdir(cwd)

    def test_passes_when_student_file_matches_model_file(self):
        with tempfile.TemporaryDirectory() as workdir:
            model_path = os.path.join(workdir, "model.txt")
            with open(model_path, "w", encoding="utf-8") as f:
                f.write("expected content\n")
            out_path = os.path.join(workdir, "out.txt")

            feedback = self._run(
                workdir, STUDENT_CODE_WRITES_FILE,
                args=[out_path, "expected content\n"], expected=True,
                file_compare={
                    "student_file": out_path,
                    "model_file": model_path,
                    "error_message": "content mismatch",
                    "file_not_found_error": "file missing",
                    "read_error": "could not read file",
                },
            )

            self.assertTrue(feedback["result"]["bool"])

    def test_fails_when_student_file_content_differs_from_model_file(self):
        with tempfile.TemporaryDirectory() as workdir:
            model_path = os.path.join(workdir, "model.txt")
            with open(model_path, "w", encoding="utf-8") as f:
                f.write("expected content\n")
            out_path = os.path.join(workdir, "out.txt")

            feedback = self._run(
                workdir, STUDENT_CODE_WRITES_FILE,
                args=[out_path, "wrong content"], expected=True,
                file_compare={
                    "student_file": out_path,
                    "model_file": model_path,
                    "error_message": "content mismatch",
                    "file_not_found_error": "file missing",
                    "read_error": "could not read file",
                },
            )

            self.assertFalse(feedback["result"]["bool"])
            result = feedback["test_results"][0]
            self.assertEqual(result["feedback"]["type"], "ContentMismatch")
            self.assertEqual(result["feedback"]["text"], "content mismatch")

    def test_fails_when_student_never_creates_the_file(self):
        with tempfile.TemporaryDirectory() as workdir:
            model_path = os.path.join(workdir, "model.txt")
            with open(model_path, "w", encoding="utf-8") as f:
                f.write("expected content\n")
            out_path = os.path.join(workdir, "out.txt")

            feedback = self._run(
                workdir, STUDENT_CODE_NO_FILE,
                args=[out_path, "expected content\n"], expected=True,
                file_compare={
                    "student_file": out_path,
                    "model_file": model_path,
                    "error_message": "content mismatch",
                    "file_not_found_error": "file missing",
                    "read_error": "could not read file",
                },
            )

            self.assertFalse(feedback["result"]["bool"])
            result = feedback["test_results"][0]
            self.assertEqual(result["feedback"]["type"], "FileNotFoundError")
            self.assertEqual(result["feedback"]["text"], "file missing")

    def test_file_never_checked_when_return_value_already_wrong(self):
        # Matches INGInious's `if file_compare and success` gate: the file
        # comparison must never run (and never overwrite the row) when the
        # return-value assertion already failed -- that failure is what
        # gets reported.
        with tempfile.TemporaryDirectory() as workdir:
            model_path = os.path.join(workdir, "model.txt")
            with open(model_path, "w", encoding="utf-8") as f:
                f.write("expected content\n")
            out_path = os.path.join(workdir, "out.txt")

            feedback = self._run(
                workdir, STUDENT_CODE_WRONG_RETURN,
                args=[out_path, "expected content\n"], expected=True,
                file_compare={
                    "student_file": out_path,
                    "model_file": model_path,
                    "error_message": "content mismatch",
                    "file_not_found_error": "file missing",
                    "read_error": "could not read file",
                },
            )

            self.assertFalse(feedback["result"]["bool"])
            result = feedback["test_results"][0]
            self.assertEqual(result["feedback"]["type"], "AssertionError")

    def test_return_value_check_still_runs_when_file_compare_absent(self):
        with tempfile.TemporaryDirectory() as workdir:
            out_path = os.path.join(workdir, "out.txt")
            student_path = self._write_student_file(workdir, STUDENT_CODE_WRITES_FILE)
            spec = {
                "id": "01-test",
                "name": "writes output",
                "description": "no file_compare configured",
                "method_name": "write_output",
                "method_signature": "write_output(path, content)",
                "test": [
                    {"type": "equal", "args": [out_path, "anything"], "expected": True,
                     "error": "did not return the expected value"}
                ],
            }

            cwd = os.getcwd()
            os.chdir(workdir)
            try:
                feedback = play_unittest(spec, student_path)
            finally:
                os.chdir(cwd)

            self.assertTrue(feedback["result"]["bool"])


class FileCompareSchemaTest(pyunit.TestCase):
    def _spec(self, file_compare):
        return {
            "id": "01-test",
            "name": "writes output",
            "description": "writes the expected content to a file",
            "method_name": "write_output",
            "test": [
                {"type": "equal", "args": [1], "expected": True, "error": "nope"}
            ],
            "file_compare": file_compare,
        }

    def test_accepts_file_compare_with_required_fields(self):
        spec = self._spec({"student_file": "./out.txt", "model_file": "./model.txt"})
        jsonschema.validate(spec, UNITTEST_JSON_SCHEMA)

    def test_rejects_file_compare_missing_model_file(self):
        spec = self._spec({"student_file": "./out.txt"})
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(spec, UNITTEST_JSON_SCHEMA)


if __name__ == "__main__":
    pyunit.main()
