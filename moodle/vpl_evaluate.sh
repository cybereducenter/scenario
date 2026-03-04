#!/bin/bash
set -u -o pipefail

# Helper: write a vpl_execution that sets grade to 0 (used on unsuccessful compilation)
set_grade_zero() {
  cat > vpl_execution <<'GRADE_EOF'
#!/bin/bash
echo "Grade :=>> 0"
exit 0
GRADE_EOF
  chmod +x vpl_execution
}

##########################################################################################
# 1) Compile
##########################################################################################
if ls *.c >/dev/null 2>&1; then
  if ! gcc -std=c11 -Wall -Wextra -O2 -o program *.c 2> compile.log; then
    echo "שגיאת קומפילציה"
    sed 's/^/ /' compile.log
    set_grade_zero
    exit 0
  fi
else
  echo "No C source files (*.c) found in working directory."
  set_grade_zero
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
