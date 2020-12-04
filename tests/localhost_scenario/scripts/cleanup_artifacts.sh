#!/bin/bash

echo "Cleaning up the data-passthrough artifact from the artifact executes tests."
echo $PWD
rm -r ${PWD}/sample_artifacts/SampleTest_*.xml
rm -r ${PWD}/sample_artifacts/SampleDummy*
ls -lrta ${PWD}/sample_artifacts/
