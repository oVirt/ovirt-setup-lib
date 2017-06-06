#!/bin/bash -xe

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
autoreconf -ivf
./configure
make clean

# TODO: FIXME: make distcheck is running 0 tests since tests are not available
# in the test directory during the distcheck call. This is a packaging issue
# which should be addressed
make check

make distcheck

# create the src.rpm
rpmbuild \
    -D "_srcrpmdir $PWD/output" \
    -D "_topmdir $PWD/rpmbuild" \
    -ts ./*.gz

# install any build requirements
yum-builddep output/*src.rpm

# create the rpms
rpmbuild \
    -D "_rpmdir $PWD/output" \
    -D "_topmdir $PWD/rpmbuild" \
    --rebuild output/*.src.rpm
