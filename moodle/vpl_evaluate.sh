#!/bin/bash
set -u -o pipefail

# =============================================================================
# VPL evaluation script
#
# Flow:
# 1. Compile the student's program.
# 2. If compilation fails:
#      - Generate vpl_execution that prints the compilation errors in HTML.
#      - Set grade = 0.
# 3. If compilation succeeds:
#      - Generate vpl_execution that runs the Scenario test framework.
#      - Scenario prints a VPL-compatible HTML report and sets the grade.
#
# Notes:
# - HTML styling is expected to come from Moodle "Additional HTML".
# - All visible output must be prefixed with "Comment :=>>" for VPL.
# =============================================================================

# -----------------------------------------------------------------------------
# Helper: handle_unsuccessful_compilation
#
# Creates a VPL execution script (vpl_execution) that:
# 1. Prints a HTML block containing the compilation errors
#    (the CSS is expected to come from Moodle Additional HTML).
# 2. Prefixes every output line with "Comment :=>>" so VPL shows it as feedback.
# 3. Sets the grade to 0.
#
# Note:
# We intentionally use <<EOF (not <<'EOF') so "$logfile" is expanded
# when generating the script, embedding the actual filename (e.g. compile.log).
# -----------------------------------------------------------------------------
handle_unsuccessful_compilation() {
  local logfile="$1"
  cat > vpl_execution <<EOF
#!/bin/bash
echo 'Comment :=>> <div class="vpl-compile-box compile-error" dir="rtl">'
echo 'Comment :=>>   <div class="vpl-compile-title">שגיאת קומפילציה</div>'
echo 'Comment :=>>   <pre class="vpl-compile-log"><code>'
sed 's/^/Comment :=>> /' "$logfile"
echo 'Comment :=>>   </code></pre>'
echo 'Comment :=>> </div>'
echo "Grade :=>> 0"
exit 0
EOF

  chmod +x vpl_execution
}

##########################################################################################
# 1) Compile
##########################################################################################
if ! clang -O2 -o program main.c -lm 2> compile.log; then
  handle_unsuccessful_compilation compile.log
  exit 0
fi

##########################################################################################
# 2) Create vpl_execution runner script
##########################################################################################
cat > vpl_execution <<'EOF'
#!/bin/bash
set -u -o pipefail

SCENARIO_BIN="/usr/local/scenario-venv/bin/scenario"
TESTDIR="tests"

if [ ! -d "$TESTDIR" ]; then
  echo "ERROR: tests/ folder not found."
  echo "Make sure execution files include tests/*.json under tests/."
  echo "Grade :=>> 0"
  exit 0
fi

##########################################################################################
# Run scenario: prints the HTML report to the screen and sets the grade
##########################################################################################
PYTHONWARNINGS=ignore "$SCENARIO_BIN" --format vpl_html -d ./program "$TESTDIR"

exit 0

EOF

chmod +x vpl_execution
