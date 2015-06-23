#!/bin/bash

set -ue

train_file=$1
model_file=$2
test_file=$3
output_file=$4


pypy beam_increment.py -train $train_file $model_file

pypy beam_increment.py -test $test_file $model_file $output_file

pypy eval.py $test_file $output_file