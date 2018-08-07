#!/bin/bash -xe

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
rm -f .coverage*
find . -name "*.py[co]" -type f -delete

DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
PACKAGER=""
if [[ "${DISTVER}" == "el" ]]; then
    PACKAGER=yum
else
    PACKAGER=dnf
fi

autoreconf -ivf
./configure
make clean
export COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc"
export COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX)
export OTOPI_DEBUG=1
export OTOPI_COVERAGE=1
make distcheck

if PYTHON3=$(which python3); then
	PYTHON=${PYTHON3} UNIT2=$(which python3-unit2) COVERAGE=$(which python3-coverage) ./configure
	export COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX)
	make clean
	make check
fi

COVERAGE=$(which coverage) || COVERAGE=$(which coverage3)

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
${COVERAGE} combine
sed -i -E "s:ovirt-setup-lib-[0-9\.\-]*(master)?/::g" .coverage
${COVERAGE} html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

mv *.tar.gz exported-artifacts
find \
    "$PWD/output" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
