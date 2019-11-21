#!/bin/bash -xe

SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
autoreconf -ivf
./configure
make clean

# Get the tarball
make dist

# create the src.rpm
rpmbuild \
    -D "_srcrpmdir $PWD/output" \
    -D "_topmdir $PWD/rpmbuild" \
    -D "release_suffix ${SUFFIX}" \
    -ts ./*.gz

# install any build requirements
yum-builddep output/*src.rpm

# create the rpms
rpmbuild \
    -D "_rpmdir $PWD/output" \
    -D "_topmdir $PWD/rpmbuild" \
    -D "release_suffix ${SUFFIX}" \
    --rebuild output/*.src.rpm

# Store any relevant artifacts in exported-artifacts for the ci system to
# archive
[[ -d exported-artifacts ]] || mkdir -p exported-artifacts
find output -iname \*rpm -exec mv "{}" exported-artifacts/ \;
mv ./*tar.gz exported-artifacts/
