#http://lists.fedoraproject.org/pipermail/devel/2011-August/155358.html
%global _hardened_build 1

%global prever beta


Summary:  DHCPv4, DHCPv6 and DDNS server from ISC
Name:     kea
#%%global VERSION %%{LVERSION}-%%{patchver}
%global LVERSION %{version}-%{prever}
#%%global VERSION %%{LVERSION}
Version:  1.3.0
Release:  1%{?dist}
License:  MPLv2.0 and Boost
URL:      http://kea.isc.org
Source0:  http://ftp.isc.org/isc/kea/%{LVERSION}/kea-%{LVERSION}.tar.gz

# http://kea.isc.org/ticket/3529
Patch0:   kea-systemd.patch
Patch1:   kea-1.3.0-hooksdir.patch

# autoreconf
BuildRequires: autoconf automake libtool
BuildRequires: boost-devel
# %%configure --with-openssl
BuildRequires: openssl-devel
# %%configure --with-dhcp-mysql
BuildRequires: mariadb-connector-c-devel
# %%configure --with-dhcp-pgsql
BuildRequires: postgresql-devel
BuildRequires: log4cplus-devel
%ifnarch s390 %{mips}
BuildRequires: valgrind-devel
%endif
BuildRequires: systemd
# src/lib/testutils/dhcp_test_lib.sh
BuildRequires: procps-ng

# %%configure --with-gtest
BuildRequires: gtest-devel

# in case you ever wanted to use %%configure --enable-generate-parser
#BuildRequires: flex bison

# in case you ever wanted to use %%configure --enable-generate-docs
#BuildRequires: elinks asciidoc plantuml

Requires: kea-libs%{?_isa} = %{version}-%{release}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd


%description
DHCP implementation from Internet Systems Consortium, Inc.
that features fully functional DHCPv4, DHCPv6 and Dynamic DNS servers.
Both DHCP servers fully support server discovery,
address assignment, renewal, rebinding and release. The DHCPv6
server supports prefix delegation. Both servers support DNS Update
mechanism, using stand-alone DDNS daemon.

%package libs
Summary: Shared libraries used by Kea DHCP server

%description libs
This package contains shared libraries used by Kea DHCP server.

%package hooks
Summary: Hooks libraries for kea
Requires: kea-libs%{?_isa} = %{version}-%{release}

%description hooks
Hooking mechanism allow Kea to load one
or more dynamically-linked libraries (known as "hooks libraries")
and, at various points in its processing ("hook points"), call
functions in them.  Those functions perform whatever custom
processing is required.

%package devel
Summary: Development headers and libraries for Kea DHCP server
Requires: kea-libs%{?_isa} = %{version}-%{release}
# to build hooks (#1335900)
Requires: boost-devel

%description devel
Header files and API documentation.

%prep
%setup -q -n kea-%{LVERSION}
%patch0 -p1 -b .systemd
%patch1 -p1 -b .hooksdir

# install leases db in /var/lib/kea/ not /var/kea/
# http://kea.isc.org/ticket/3523
sed -i -e 's|@localstatedir@|@sharedstatedir@|g' src/lib/dhcpsrv/Makefile.am

# to be able to build on ppc64(le)
# https://sourceforge.net/p/flex/bugs/197
# https://lists.isc.org/pipermail/kea-dev/2016-January/000599.html
sed -i -e 's|ECHO|YYECHO|g' src/lib/eval/lexer.cc

%build
autoreconf --verbose --force --install
export CXXFLAGS="%{optflags} -std=gnu++11 -Wno-deprecated-declarations"

%configure \
    --disable-dependency-tracking \
    --disable-rpath \
    --disable-silent-rules \
    --disable-static \
    --enable-debug \
    --enable-systemd \
    --with-dhcp-mysql \
    --with-dhcp-pgsql \
    --with-gnu-ld \
    --with-log4cplus \
    --with-openssl \
#    --with-gtest

make %{?_smp_mflags}


%check
#make check

%install
make DESTDIR=%{buildroot} install %{?_smp_mflags}

# Get rid of .la files
find %{buildroot} -type f -name "*.la" -delete -print

# Start empty lease databases
mkdir -p %{buildroot}%{_sharedstatedir}/kea/
touch %{buildroot}%{_sharedstatedir}/kea/kea-leases4.csv
touch %{buildroot}%{_sharedstatedir}/kea/kea-leases6.csv

rm -f %{buildroot}%{_pkgdocdir}/COPYING

mkdir -p %{buildroot}/run
install -d -m 0755 %{buildroot}/run/kea/

# install /usr/lib/tmpfiles.d/kea.conf
mkdir -p %{buildroot}%{_tmpfilesdir}
cat > %{buildroot}%{_tmpfilesdir}/kea.conf <<EOF
# kea needs existing /run/kea/ to create logger_lockfile there
# See tmpfiles.d(5) for details

d /run/kea 0755 root root -
EOF


%post
%systemd_post kea-dhcp4.service kea-dhcp6.service kea-dhcp-ddns.service


%preun
%systemd_preun kea-dhcp4.service kea-dhcp6.service kea-dhcp-ddns.service


%postun
%systemd_postun_with_restart kea-dhcp4.service kea-dhcp6.service kea-dhcp-ddns.service


%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig


%files
%{_sbindir}/kea-admin
%{_sbindir}/kea-dhcp-ddns
%{_sbindir}/kea-dhcp4
%{_sbindir}/kea-dhcp6
%{_sbindir}/kea-lfc
%{_sbindir}/keactrl
%{_sbindir}/perfdhcp
%{_bindir}/kea-msg-compiler
%{_sbindir}/kea-ctrl-agent
%{_unitdir}/kea-dhcp4.service
%{_unitdir}/kea-dhcp6.service
%{_unitdir}/kea-dhcp-ddns.service
%dir %{_sysconfdir}/kea/
%config(noreplace) %{_sysconfdir}/kea/kea.conf
%config(noreplace) %{_sysconfdir}/kea/keactrl.conf
%dir %{_datarootdir}/kea/
%{_datarootdir}/kea/scripts
%dir /run/kea/
%{_tmpfilesdir}/kea.conf
%{_datarootdir}/kea/dhcp-ddns.spec
%{_datarootdir}/kea/dhcp4.spec
%{_datarootdir}/kea/dhcp6.spec
%dir %{_sharedstatedir}/kea
%config(noreplace) %{_sharedstatedir}/kea/kea-leases4.csv
%config(noreplace) %{_sharedstatedir}/kea/kea-leases6.csv
%{_pkgdocdir}/AUTHORS
%{_pkgdocdir}/ChangeLog
%{_pkgdocdir}/README
%{_pkgdocdir}/examples
%{_pkgdocdir}/kea-guide.*
%{_pkgdocdir}/kea-logo-100x70.png
%{_pkgdocdir}/kea-messages.html
%{_mandir}/man8/kea-admin.8.gz
%{_mandir}/man8/kea-dhcp-ddns.8.gz
%{_mandir}/man8/kea-dhcp4.8.gz
%{_mandir}/man8/kea-dhcp6.8.gz
%{_mandir}/man8/kea-lfc.8.gz
%{_mandir}/man8/keactrl.8.gz
%{_mandir}/man8/perfdhcp.8.gz
%{_mandir}/man8/kea-ctrl-agent.8.gz
%{_mandir}/man8/kea-shell.8.gz

%files hooks
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/hooks

%files libs
#%%dir %%{_pkgdocdir}/
#%%{_pkgdocdir}/COPYING
#%%{_pkgdocdir}/LICENSE_1_0.txt
%license COPYING
%license ext/coroutine/LICENSE_1_0.txt
%{_libdir}/libkea-asiodns.so.*
%{_libdir}/libkea-asiolink.so.*
%{_libdir}/libkea-cc.so.*
%{_libdir}/libkea-cfgclient.so.*
%{_libdir}/libkea-cryptolink.so.*
%{_libdir}/libkea-dhcp++.so.*
%{_libdir}/libkea-dhcp_ddns.so.*
%{_libdir}/libkea-dhcpsrv.so.*
%{_libdir}/libkea-dns++.so.*
%{_libdir}/libkea-eval.so.*
%{_libdir}/libkea-exceptions.so.*
%{_libdir}/libkea-hooks.so.*
%{_libdir}/libkea-log.so.*
%{_libdir}/libkea-stats.so.*
%{_libdir}/libkea-threads.so.*
%{_libdir}/libkea-util-io.so.*
%{_libdir}/libkea-util.so.*
%{_libdir}/libkea-http.so
%{_libdir}/libkea-http.so.0
%{_libdir}/libkea-http.so.0.0.0
%{_libdir}/libkea-process.so
%{_libdir}/libkea-process.so.0
%{_libdir}/libkea-process.so.0.0.0

%files devel
%{_includedir}/kea
%{_libdir}/libkea-asiodns.so
%{_libdir}/libkea-asiolink.so
%{_libdir}/libkea-cc.so
%{_libdir}/libkea-cfgclient.so
%{_libdir}/libkea-cryptolink.so
%{_libdir}/libkea-dhcp++.so
%{_libdir}/libkea-dhcp_ddns.so
%{_libdir}/libkea-dhcpsrv.so
%{_libdir}/libkea-dns++.so
%{_libdir}/libkea-eval.so
%{_libdir}/libkea-exceptions.so
%{_libdir}/libkea-hooks.so
%{_libdir}/libkea-log.so
%{_libdir}/libkea-stats.so
%{_libdir}/libkea-threads.so
%{_libdir}/libkea-util-io.so
%{_libdir}/libkea-util.so
%{_libdir}/pkgconfig/dns++.pc

%changelog
* Mon Oct 23 2017 Pavel Zhukov <pzhukov@redhat.com> - 1.2.0-8
- Require openssl102

* Sun Oct 22 2017 Pavel Zhukov <pzhukov@redhat.com> - 1.2.0-7
- Rebuild with new openssl

* Thu Oct 12 2017 Pavel Zhukov <pzhukov@redhat.com> - 1.2.0-6
- Use mariadb-connector-c-devel instead of mysql-devel (#1493628)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jul 03 2017 Jonathan Wakely <jwakely@redhat.com> - 1.2.0-3
- Rebuilt for Boost 1.64

* Fri May 26 2017 Pavel Zhukov <landgraf@fedoraproject.org> - 1.2.0-2
- New release 1.2.0 (#1440348)

* Tue Apr 04 2017 Pavel Zhukov <landgraf@fedoraproject.org> - 1.1.0-3
- Add patch for OpenSSL 1.1. Fix FTBFS (#1423812)

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Oct 04 2016 Jiri Popelka <jpopelka@redhat.com> - 1.1.0-1
- 1.1.0

* Thu Sep 01 2016 Jiri Popelka <jpopelka@redhat.com> - 1.1.0-0.1
- 1.1.0-beta

* Fri Aug 12 2016 Michal Toman <mtoman@fedoraproject.org> - 1.0.0-11
- No valgrind on MIPS

* Wed Aug 03 2016 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-10
- %%{_defaultdocdir}/kea/ -> %%{_pkgdocdir}

* Fri May 13 2016 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-9
- devel subpackage Requires: boost-devel

* Wed Mar 23 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.0.0-8
- Rebuild for log4cplus-1.2.0-2

* Wed Mar 23 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.0.0-7
- Rebuilding kea for log4cplus-1.2.0

* Wed Mar 16 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.0.0-6
- Editing pgsql_lease_mgr.cc according to upstream

* Fri Mar 11 2016 Zdenek Dohnal <zdohnal@redhat.com> - 1.0.0-4
- Fixing bugs created from new C++ standard

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jan 15 2016 Jonathan Wakely <jwakely@redhat.com> - 1.0.0-2
- Rebuilt for Boost 1.60

* Tue Dec 29 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-1
- 1.0.0

* Wed Dec 23 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-0.3.beta2
- fix compile error

* Wed Dec 23 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-0.2.beta2
- 1.0.0-beta2

* Wed Dec 09 2015 Jiri Popelka <jpopelka@redhat.com> - 1.0.0-0.1.beta
- 1.0.0-beta

* Mon Aug 24 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.2-3
- fix valgrind-devel availability

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.2-2
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Tue Jul 28 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.2-1
- 0.9.2

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com> - 0.9.2-0.2.beta
- rebuild for Boost 1.58

* Thu Jul 02 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.2-0.1.beta
- 0.9.2-beta

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 0.9.1-2
- Rebuilt for GCC 5 C++11 ABI change

* Wed Apr 01 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.1-1
- 0.9.1

* Fri Feb 20 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.1-0.2.beta
- /run/kea/ (for logger_lockfile)

* Thu Feb 19 2015 Jiri Popelka <jpopelka@redhat.com> - 0.9.1-0.1.beta
- 0.9.1-beta

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 0.9-4
- Rebuild for boost 1.57.0

* Tue Nov 04 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-3
- do not override @localstatedir@ globally
- include latest upstream kea.conf

* Wed Sep 24 2014 Dan Horák <dan[at]danny.cz> - 0.9-2
- valgrind available only on selected arches

* Mon Sep 01 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-1
- 0.9

* Thu Aug 21 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-0.5.beta1
- fix building with PostgreSQL on i686
- redefine localstatedir to sharedstatedir (kea#3523)

* Wed Aug 20 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-0.4.beta1
- install systemd service units with a proper patch that we can send upstream
- build with MySQL & PostgreSQL & Google Test
- no need to copy sample configuration, /etc/kea/kea.conf already contains one

* Tue Aug 19 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-0.3.beta1
- comment patches
- use --preserve-timestamps with install

* Mon Aug 18 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-0.2.beta1
- make it build on armv7
- BuildRequires procps-ng for %%check
- use install instead of cp
- configure.ac: AC_PROG_LIBTOOL -> LT_INIT
- move license files to -libs

* Thu Aug 14 2014 Jiri Popelka <jpopelka@redhat.com> - 0.9-0.1.beta1
- initial spec
