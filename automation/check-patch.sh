#!/bin/bash -xe

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz

#for some reason looks like otopi is not getting installed by STD ci scripts
yum -y install otopi

autoreconf -ivf
./configure
make clean
export COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc"
export COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX)
export OTOPI_DEBUG=1
export OTOPI_COVERAGE=1
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

unset COVERAGE_FILE
coverage combine
sed -i "s:ovirt-setup-lib-[0-9\.\-]*master/::g" .coverage
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/
