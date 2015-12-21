include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

dist_noinst_PYTHON = \
	__init__.py \
	commons.py \
	test_hostname.py

check: \
	python-check \
	python-syntax-check \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)
