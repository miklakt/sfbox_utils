#!/bin/bash

# Output files from sfbox may contains results for multiple sequential
# calculations divided by 'system delimiter' string. The scripts splits the file
# into multiple ones which contain only one calculation.

mkdir "${1%.*}_tmp"
cd "${1%.*}_tmp"
csplit "../$1" -n3 '/system delimiter/' '{*}' --suppress-matched --prefix "${1%.*}" --suffix-format "_%03d.out"