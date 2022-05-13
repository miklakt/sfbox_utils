#!/bin/bash
mkdir "${1%.*}_tmp"
cd "${1%.*}_tmp"
csplit "../$1" -n3 '/system delimiter/' '{*}' --suppress-matched --prefix "${1%.*}" --suffix-format "_%03d.out"