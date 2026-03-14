#!/bin/bash
set -u

# hard safety: never allow cases evaluator file to exist
rm -f vpl_evaluate.cases

for f in *_qvpl; do
  [ -e "$f" ] || continue

  # Never rename anything into vpl_evaluate.cases
  if [ "$f" = "vpl_evaluate.cases_qvpl" ]; then
    continue
  fi

  out="${f%_qvpl}"
  mv -- "$f" "$out"
done
