#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.60])
define([VERSION_MAJOR], [1])
define([VERSION_MINOR], [3])
define([VERSION_FIX], [4])
define([VERSION_NUMBER], VERSION_MAJOR[.]VERSION_MINOR[.]VERSION_FIX)
define([VERSION_RELEASE], [1])
define([VERSION_SUFFIX], [])

AC_INIT([ovirt-setup-lib], [VERSION_NUMBER], [devel@ovirt.org])
PACKAGE_RPM_VERSION="VERSION_NUMBER"
PACKAGE_RPM_RELEASE="VERSION_RELEASE"
AC_SUBST([PACKAGE_RPM_VERSION])
AC_SUBST([PACKAGE_RPM_RELEASE])

AC_CONFIG_AUX_DIR([.])
AC_CONFIG_SRCDIR([src/ovirt_setup_lib/__init__.py])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE([1.9])
AM_GNU_GETTEXT_VERSION([0.17])
AM_PO_SUBDIRS

AC_ARG_ENABLE(
	[python-syntax-check],
	[AS_HELP_STRING([--disable-python-syntax-check], [disable python syntax check @<:@default=enabled@:>@])],
	,
	[enable_python_syntax_check="yes"]
)

AC_PROG_INSTALL

AC_ARG_VAR([PYFLAKES], [path to pyflakes utility])
AC_CHECK_PROGS([PYFLAKES], [pyflakes])
AC_ARG_VAR([PEP8], [path to pep8 utility])
AC_CHECK_PROGS([PEP8], [pycodestyle-3 pep8])
AC_ARG_VAR([COVERAGE], [path to coverage utility])
AC_CHECK_PROGS([COVERAGE], [coverage-3 coverage])

AM_PATH_PYTHON([3.6],, [AC_MSG_ERROR([Cannot find python])])
AM_CONDITIONAL([PYTHON_SYNTAX_CHECK], [test "${enable_python_syntax_check}" = "yes"])

ovirtsetuplibdir="\$(pythondir)/ovirt_setup_lib"
AC_SUBST([ovirtsetuplibdir])

AC_CONFIG_FILES([
	Makefile
	build/Makefile
	po/Makefile.in
	src/Makefile
	src/ovirt_setup_lib/Makefile
	tests/Makefile
	ovirt-setup-lib.spec
])
AC_OUTPUT
