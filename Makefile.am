
AUTOMAKE_OPTIONS = foreign 1.9
ACLOCAL_AMFLAGS = -I m4

MAINTAINERCLEANFILES = \
	config.log config.status \
	$(srcdir)/Makefile.in \
	$(srcdir)/configure \
	$(srcdir)/install-sh $(srcdir)/missing \
	$(srcdir)/depcomp $(srcdir)/py-compile \
	$(srcdir)/config.guess $(srcdir)/config.sub \
	$(srcdir)/config.rpath \
	$(srcdir)/ABOUT-NLS \
	$(srcdir)/aclocal.m4 \
	$(NULL)
CLEANFILES = \
	POTFILES.in.tmp \
	$(NULL)

EXTRA_DIST = \
	.gitignore \
	po/.gitignore \
	$(NULL)

SUBDIRS = \
	build \
	po \
	src \
	tests \
	$(NULL)

dist_noinst_DATA = \
	ovirt-setup-lib.spec \
	$(NULL)

dist_doc_DATA = \
	README.md
	$(NULL)

maintainer-clean-local:
	sed '/^$$/d' "$(srcdir)/m4/.gitignore" | while read f; do \
		rm -f $(srcdir)/m4/$$f; \
	done
	sed '/^$$/d' "$(srcdir)/po/.gitignore" | while read f; do \
		rm -f $(srcdir)/po/$$f po/$$f; \
	done

POTFILES.in:
	( cd "$(srcdir)" && \
		find ./src -name '*.py' -or -name '*.py.in' ) | \
		sort | grep -v config.py > POTFILES.in.tmp && \
	cmp -s POTFILES.in.tmp "$(srcdir)/po/POTFILES.in" || \
		cp POTFILES.in.tmp "$(srcdir)/po/POTFILES.in"; \
	rm -f POTFILES.in.tmp

update-po: POTFILES.in
	$(MAKE) -C po update-po

TMPREPOS = tmp.repos
RPMBUILD_ARGS := --define="_topdir `pwd`/$(TMPREPOS)"
RPMBUILD_ARGS += $(if $(RELEASE_SUFFIX),--define="release_suffix $(RELEASE_SUFFIX)")

rpm: srpm
	rpmbuild $(RPMBUILD_ARGS) --rebuild "$(TMPREPOS)"/SRPMS/*.src.rpm
	cp $(distdir).tar.gz $(TMPREPOS)/SOURCES/
	@echo
	@echo "rpm available at '$(TMPREPOS)'"
	@echo

srpm: dist
	rm -rf "$(TMPREPOS)"
	mkdir -vp $(TMPREPOS)/{SPECS,RPMS,SRPMS,SOURCES}
	rpmbuild $(RPMBUILD_ARGS) -ts $(distdir).tar.gz
	@echo
	@echo "srpm available at '$(TMPREPOS)'"

.PHONY: rpm srpm
