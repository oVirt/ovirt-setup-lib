#!/bin/bash -xe

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz
rm -f .coverage*
find . -name "*.py[co]" -type f -delete

DISTVER="$(rpm --eval "%dist"|cut -c2-4)"
PACKAGER=""
if [[ "${DISTVER}" == "el7" ]]; then
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

COVERAGE=$(which coverage) || COVERAGE=$(which coverage3) || COVERAGE=$(which coverage-3)
export COVERAGE
if PYTHON3=$(which python3); then
	PYTHON=${PYTHON3} UNIT2=$(which python3-unit2)  ./configure
	export COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX)
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
${COVERAGE} combine
sed -i -E "s:ovirt-setup-lib-[0-9\.\-]*(master)?/::g" .coverage
sed -i -E "s:ovirt-setup-lib-[0-9\.\-]*(alpha[0-9]*)?/::g" .coverage
sed -i -E "s:ovirt-setup-lib-[0-9\.\-]*(beta[0-9]*)?/::g" .coverage
${COVERAGE} html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

mv *.tar.gz exported-artifacts
find \
    "$PWD/output" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
