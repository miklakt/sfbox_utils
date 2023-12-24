#!/bin/bash

# The script runs up to 'cpu_count' sfbox processes in parallel, 
# until all files with mask '*.in' are processed.

cpu_count=$1
executable=$2
echo "running sfbox with multiple input files"
echo "max processes: $cpu_count"
echo "executable path: $executable"
find . -type f -iname "*.in" -execdir sh -c 'printf "%s\n" "${0%.*}"' {} ';' | xargs -I{} -P $cpu_count sh -c "echo started {}; $executable {}.in > {}.log; echo done {};"
echo "Done!"