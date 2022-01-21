
PYTHON_SYNTAX_CHECK_FILES = $(srcdir)/*.py

python-syntax-check:
if PYTHON_SYNTAX_CHECK
	if [ -n "$(PYFLAKES)" ]; then \
		$(PYFLAKES) $(PYTHON_SYNTAX_CHECK_FILES); \
	fi
	if [ -n "$(PEP8)" ]; then \
		$(PEP8) $(PYTHON_SYNTAX_CHECK_FILES); \
	fi
endif

python-clean:
	rm -rf $(srcdir)/__pycache__ __pycache__
	rm -f $(srcdir)/*.pyc $(srcdir)/*.pyo *.pyc *.pyo

python-check:
	if [ -n "$(COVERAGE)" ]; then \
		PYTHONPATH="$(top_srcdir)/src:$$PYTHONPATH" $(COVERAGE) run --omit="/usr/bin/*","/usr/lib*/python*/site-packages/*" -m unittest discover -v $(srcdir); \
	else \
		PYTHONPATH="$(top_srcdir)/src:$$PYTHONPATH" $(PYTHON) -m unittest discover -v $(srcdir); \
	fi
