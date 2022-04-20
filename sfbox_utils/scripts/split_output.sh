#!/bin/bash
mkdir "${1%.*}"
cd "${1%.*}"
csplit "../$1" -n3 '/system delimiter/' '{*}' --suppress-matched --prefix "${1%.*}" --suffix-format "_%03d.out"