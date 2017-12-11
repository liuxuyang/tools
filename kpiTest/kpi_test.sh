#!/usr/bin/env bash
command -v python >/dev/null 2>&1 || \
    echo ">> Require python executable to be in path" >&2

python -V 2>&1 | grep -q "Python 2.7" || \
    echo ">> Require python 2.7" >&2

function print_err(){
    echo ">> Require Python ${1} module,you can install ${1} with 'pip install ${1}'"
    exit
}

for M in openpyxl matplotlib
do
    python -c "import $M" >/dev/null 2>&1 || print_err ${M}

done

cur_path=$(cd `dirname $0`;pwd)
export PYTHONPATH="${cur_path}/data:$PYTHONPATH"
export PYTHONPATH="${cur_path}/tool:$PYTHONPATH"
python ${cur_path}'/kpi_test.py' $*