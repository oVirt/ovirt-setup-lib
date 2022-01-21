#!/bin/bash -xe

SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

# mock runner is not setting up the system correctly
# https://issues.redhat.com/browse/CPDEVOPS-242
dnf install -y $(cat automation/check-patch.packages)

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
autopoint
autoreconf -ivf
./configure
make clean

# Get the tarball
make dist

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

# Store any relevant artifacts in exported-artifacts for the ci system to
# archive
[[ -d exported-artifacts ]] || mkdir -p exported-artifacts
find output -iname \*rpm -exec mv "{}" exported-artifacts/ \;
mv ./*tar.gz exported-artifacts/
