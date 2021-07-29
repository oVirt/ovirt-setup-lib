#!/bin/bash -xe

# mock runner is not setting up the system correctly
# https://issues.redhat.com/browse/CPDEVOPS-242
dnf install -y $(cat automation/check-patch.packages)

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
rm -f .coverage*
find . -name "*.py[co]" -type f -delete

autopoint
autoreconf -ivf
./configure
make clean
export COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc"
COVERAGE_FILE=$(mktemp -p "$PWD" .coverage.XXXXXX)
export COVERAGE_FILE
export OTOPI_DEBUG=1
export OTOPI_COVERAGE=1
make distcheck

COVERAGE=$(which coverage) || COVERAGE=$(which coverage3) || COVERAGE=$(which coverage-3)
export COVERAGE
if PYTHON3=$(which python3); then
	PYTHON=${PYTHON3} UNIT2=$(which python3-unit2)  ./configure
    COVERAGE_FILE=$(mktemp -p "$PWD" .coverage.XXXXXX)
	export COVERAGE_FILE
	make clean
	make check
fi



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
# extract tarball to make src available to coverage
tar xzf ./*.tar.gz
${COVERAGE} combine
${COVERAGE} html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

mv ./*.tar.gz exported-artifacts
find \
    "$PWD/output" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
