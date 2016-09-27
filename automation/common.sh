# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz

[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

# On fedora 23 and up, we want to use python3
distribution_name="$(python -c "import platform; print(platform.linux_distribution(full_distribution_name=0)[0])")"
distribution_version="$(python -c "import platform; print(platform.linux_distribution(full_distribution_name=0)[1])")"
if [ "${distribution_name}" == "fedora" -a "${distribution_version}" -ge 23 ]; then
	DEVPKG=python3-devel
	PEP8PKG=python3-pep8
	FLAKGESPKG=python3-pyflakes
	PEP8=/usr/bin/python3-pep8
	PYFLAKES=/usr/bin/python3-pyflakes
	PYTHON=/usr/bin/python3
else
	DEVPKG=python2-devel
	PEP8PKG=python-pep8
	FLAKGESPKG=pyflakes
	PEP8=/usr/bin/pep8
	PYFLAKES=/usr/bin/pyflakes
	PYTHON=/usr/bin/python
fi
export PEP8 PYFLAKES PYTHON
yum install -y $DEVPKG $PEP8PKG $FLAKGESPKG $COVPKG

autoreconf -ivf
./configure
make clean

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

find \
    "$PWD/output" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;

