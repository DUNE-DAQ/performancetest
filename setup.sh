PERFORMANCE_TEST_PATH=`realpath $BASH_SOURCE | xargs dirname`
export PERFORMANCE_TEST_PATH
export PATH=$PERFORMANCE_TEST_PATH/tools:$PATH
export PATH=$PERFORMANCE_TEST_PATH/scripts:$PATH
export PATH=$PERFORMANCE_TEST_PATH/tests:$PATH
echo "performance test executables added to PATH"