#!/bin/bash

set -ue

train_file=$1
test_file=$2
model_file=$3
output_file=$4
size=$5

pypy beam_increment.py -train $train_file $model_file $size

pypy beam_increment.py -test $test_file $model_file $output_file $size

pypy eval.py $test_file $output_file