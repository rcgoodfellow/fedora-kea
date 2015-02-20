#http://lists.fedoraproject.org/pipermail/devel/2011-August/155358.html
%global _hardened_build 1

%global prever beta

#%%global VERSION %{version}-%{patchver}
#%%global VERSION %{version}
%global VERSION %{version}-%{prever}

Summary:  DHCPv4, DHCPv6 and DDNS server from ISC
Name:     kea
Version:  0.9.1
Release:  0.2.%{prever}%{?dist}
License:  ISC and Boost
URL:      http://kea.isc.org
Source0:  http://ftp.isc.org/isc/kea/%{VERSION}/kea-%{VERSION}.tar.gz

# http://kea.isc.org/ticket/3529
Patch0:   kea-systemd.patch

# autoreconf
BuildRequires: autoconf automake libtool
BuildRequires: boost-devel
# %%configure --with-openssl
BuildRequires: openssl-devel
# %%configure --with-dhcp-mysql
BuildRequires: mariadb-devel
# %%configure --with-dhcp-pgsql
BuildRequires: postgresql-devel
BuildRequires: log4cplus-devel
%ifarch %{ix86} x86_64 ppc ppc64 ppc64le s390x armv7hl aarch64
BuildRequires: valgrind-devel
%endif
BuildRequires: systemd
# src/lib/testutils/dhcp_test_lib.sh
BuildRequires: procps-ng


# %%configure --enable-gtest
BuildRequires: gtest-devel
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

%package devel
Summary: Development headers and libraries for Kea DHCP server
Requires: kea-libs%{?_isa} = %{version}-%{release}

%description devel
Header files and API documentation.

%prep
%setup -q -n kea-%{VERSION}

%patch0 -p1 -b .systemd

# install leases db in /var/lib/kea/ not /var/kea/
# http://kea.isc.org/ticket/3523
sed -i -e 's|@localstatedir@|@sharedstatedir@|g' src/lib/dhcpsrv/Makefile.am

%build
autoreconf --verbose --force --install

%configure \
    --disable-silent-rules \
    --disable-dependency-tracking \
    --disable-static \
    --enable-systemd \
    --with-openssl \
    --with-dhcp-mysql \
    --with-dhcp-pgsql \
    --disable-rpath \
    --enable-gtest \
    --enable-debug

make %{?_smp_mflags}


%check
#make check


%install
make install DESTDIR=%{buildroot}

# Get rid of .la files
rm -f %{buildroot}%{_libdir}/libkea-*.la

# Start empty lease databases
mkdir -p %{buildroot}%{_sharedstatedir}/kea/
touch %{buildroot}%{_sharedstatedir}/kea/kea-leases4.csv
touch %{buildroot}%{_sharedstatedir}/kea/kea-leases6.csv

install -p -m 644 ext/LICENSE_1_0.txt %{buildroot}%{_defaultdocdir}/kea/

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
%{_unitdir}/kea-dhcp4.service
%{_unitdir}/kea-dhcp6.service
%{_unitdir}/kea-dhcp-ddns.service
%dir %{_sysconfdir}/kea/
%config(noreplace) %{_sysconfdir}/kea/kea.conf
%config(noreplace) %{_sysconfdir}/kea/keactrl.conf
%dir %{_datarootdir}/kea/
%dir %{_datarootdir}/kea/scripts/
%dir %{_datarootdir}/kea/scripts/mysql/
%dir %{_datarootdir}/kea/scripts/pgsql/
%dir /run/kea/
%{_tmpfilesdir}/kea.conf
%{_datarootdir}/kea/dhcp-ddns.spec
%{_datarootdir}/kea/dhcp4.spec
%{_datarootdir}/kea/dhcp6.spec
%{_datarootdir}/kea/scripts/admin-utils.sh
%{_datarootdir}/kea/scripts/mysql/dhcpdb_create.mysql
%{_datarootdir}/kea/scripts/mysql/upgrade_1.0_to_2.0.sh
%{_datarootdir}/kea/scripts/pgsql/dhcpdb_create.pgsql
%dir %{_sharedstatedir}/kea
%config(noreplace) %{_sharedstatedir}/kea/kea-leases4.csv
%config(noreplace) %{_sharedstatedir}/kea/kea-leases6.csv
%{_defaultdocdir}/kea/AUTHORS
%{_defaultdocdir}/kea/ChangeLog
%{_defaultdocdir}/kea/README
%{_defaultdocdir}/kea/examples
%{_defaultdocdir}/kea/kea-guide.*
%{_defaultdocdir}/kea/kea-messages.html
%{_mandir}/man8/kea-admin.8.gz
%{_mandir}/man8/kea-dhcp-ddns.8.gz
%{_mandir}/man8/kea-dhcp4.8.gz
%{_mandir}/man8/kea-dhcp6.8.gz
%{_mandir}/man8/kea-lfc.8.gz
%{_mandir}/man8/keactrl.8.gz
%{_mandir}/man8/perfdhcp.8.gz

%files libs
%dir %{_defaultdocdir}/kea/
%{_defaultdocdir}/kea/COPYING
%{_defaultdocdir}/kea/LICENSE_1_0.txt
%{_libdir}/libkea-asiodns.so.*
%{_libdir}/libkea-asiolink.so.*
%{_libdir}/libkea-cc.so.*
%{_libdir}/libkea-cfgclient.so.*
%{_libdir}/libkea-cryptolink.so.*
%{_libdir}/libkea-dhcp++.so.*
%{_libdir}/libkea-dhcp_ddns.so.*
%{_libdir}/libkea-dhcpsrv.so.*
%{_libdir}/libkea-dns++.so.*
%{_libdir}/libkea-exceptions.so.*
%{_libdir}/libkea-hooks.so.*
%{_libdir}/libkea-log.so.*
%{_libdir}/libkea-threads.so.*
%{_libdir}/libkea-util-io.so.*
%{_libdir}/libkea-util.so.*

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
%{_libdir}/libkea-exceptions.so
%{_libdir}/libkea-hooks.so
%{_libdir}/libkea-log.so
%{_libdir}/libkea-threads.so
%{_libdir}/libkea-util-io.so
%{_libdir}/libkea-util.so
%{_libdir}/pkgconfig/dns++.pc

%changelog
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
