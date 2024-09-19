MY_DIR=`realpath $BASH_SOURCE | xargs dirname`
export MY_DIR
export PATH=$MY_DIR/tools:$PATH
export PATH=$MY_DIR/scripts:$PATH
export PATH=$MY_DIR/tests:$PATH
echo "performance test executables added to PATH"

unset MY_DIR