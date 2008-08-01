Summary:	Accounting software
Name:		quasar
Version:	1.4.7_GPL
Release:	%mkrel 11
License:	GPLv2
Group:		Office
URL:		http://www.linuxcanada.com
Source0:	ftp://ftp.linuxcanada.com/pub/Quasar/1.4.7/source/%{name}-%{version}.tar.bz2
Source1:	ftp://ftp.linuxcanada.com/pub/Quasar/1.4.7/manuals/quasar_install-1.4.7.pdf
Source2:	ftp://ftp.linuxcanada.com/pub/Quasar/1.4.7/manuals/quasar_guide-1.4.7.pdf
Source3:	ftp://ftp.linuxcanada.com/pub/Quasar/1.4.7/manuals/quasar_reference-1.4.7.pdf
Source4:	ftp://ftp.linuxcanada.com/pub/Quasar/1.4.7/manuals/quasar_features-1.4.7.pdf
Patch0:		quasar-1.4.7_GPL-not-in-opt.patch
# Use lockf, not flock, as x86_64 appears to have trouble with flock
# - AdamW 2008/01
Patch1:		quasar-1.4.7_GPL-lockf.patch
# Use #ifdef __linux__, not #ifdef LINUX, as this breaks build on
# x86-64 - AdamW 2008/01
Patch2:		quasar-1.4.7_GPL-ifdeflinux.patch
# .pro files have special definitions for 'linux-g++', but when
# building on x86-64, we're 'linux-g++-64' - so duplicate the
# definitions for that platform - AdamW 2008/01
Patch3:		quasar-1.4.7_GPL-x86_64_defs.patch
# Use -fPIC for build, otherwise fails on x86-64 - AdamW 2008/01
Patch4:		quasar-1.4.7_GPL-fpic.patch
# Fix some variable problems which prevent firebird driver building
# on x86-64 (thanks Anssi) - AdamW 2008/01
Patch5:		quasar-1.4.7_GPL-firebird_x86_64.patch
BuildRequires:	qt3-devel 
BuildRequires:	tk tk-devel
BuildRequires:	tcl tcl-devel
BuildRequires:	postgresql-devel 
BuildRequires:	firebird-devel 
BuildRequires:	libicu-devel
BuildRequires:	xinetd
Buildroot:	%{_tmppath}/%{name}-%{version}-root

%description
There is no package without a qualifier so this is not built.

%package	server
Summary:	Accounting software
Group:		Office
Requires:	tcl xinetd
Requires(pre):	rpm-helper

%description	server
Quasar is a business accounting package for Linux and Windows. This
package installs the server that Quasar client connect to.  The
company databases reside on the server and are shared by all the 
clients.

%package	client
Summary:	Accounting software
Group:		Office
Provides:	quasar
Requires:	tcl usermode usermode-consoleonly
Requires(pre):	rpm-helper

%description	client
Quasar is a business accounting package for Linux and Windows.  
This package installs the GUI client part of Quasar.

%package	doc
Summary:	Accounting software
Group:		Office

%description	doc
Quasar is a business accounting package for Linux and Windows.  
This package installs additional Quasar docmentation.

%prep

%setup -q
%patch0 -p1 -b .notinopt
%patch1 -p1 -b .lockf
%patch2 -p1 -b .ifdeflinux
%patch3 -p1 -b .x86_64_deps
%patch4 -p1 -b .fpic
%patch5 -p1 -b .firebird_x86_64

cp %{SOURCE1} %{SOURCE2} %{SOURCE3} %{SOURCE4} .

%build
%configure2_5x --with-firebird=%{_prefix}
%make all

cat > %{name}-server.logrotate <<EOF
/var/log/quasar/*.log {
    notifempty
    missingok
    sharedscripts
    copytruncate
    postrotate
        /usr/bin/killall -HUP quasard; /usr/bin/killall -HUP quasar-clientd; 
    endscript
}
EOF

%install
rm -rf %{buildroot}
%make install PREFIX=%{buildroot} LIBDIR=%{_libdir}
install -d %{buildroot}%{_logdir}/%{name}

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
install -m644 %{name}-server.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}-server

# (sb) rpmlint happiness
chmod 0644 %{buildroot}%{_sysconfdir}/%{name}/*.cfg
chmod 0755 %{buildroot}%{_libdir}/%{name}/drivers/*
chmod 0755 %{buildroot}%{_localstatedir}/lib/%{name}/databases

# setup links for consolehelpper support to allow root setup
pushd %{buildroot}%{_bindir}
ln -sf consolehelper %{name}_setup
popd

install -d %{buildroot}%{_sysconfdir}/pam.d

cat << EOF > %{buildroot}%{_sysconfdir}/pam.d/%{name}_setup
#%PAM-1.0
auth       sufficient   pam_rootok.so
auth       include  system-auth
account    required pam_permit.so
session    optional pam_xauth.so
EOF

mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/mandriva-%{name}-setup.desktop << EOF
[Desktop Entry]
Name=Quasar Setup
Comment=Quasar Accounting Software - Setup
Exec=%{_bindir}/quasar_setup
Icon=finances_section
Terminal=false
Type=Application
Categories=Office;Finance;
EOF

cat > %{buildroot}%{_datadir}/applications/mandriva-%{name}.desktop << EOF
[Desktop Entry]
Name=Quasar
Comment=Quasar Accounting Software
Exec=%{_bindir}/quasar
Icon=finances_section
Terminal=false
Type=Application
Categories=Office;Finance;
EOF

%clean
rm -rf %{buildroot}

%pre server
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/bash

%post server
if [ "$1" = 1 ]; then
    chown -R quasar %{_logdir}/%{name}
    chgrp -R quasar %{_logdir}/%{name}

    # Set file ownership and permissions
    chgrp -R quasar %{_sysconfdir}/%{name}
    chgrp -R quasar %{_localstatedir}/lib/%{name}/data

    # Restart xinetd so it find new quasar entry
    /etc/init.d/xinetd restart
fi

%postun server
if [ "$1" = 0 ]; then
    # Restart xinetd so it find quasar is gone
    /etc/init.d/xinetd restart
fi

%pre client
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/bash

%post client
if [ "$1" = 1 ]; then
    # Set file ownership and permissions
    chgrp -R %{name} %{_sysconfdir}/%{name}
fi
%if %mdkversion < 200900
%{update_menus}
%endif

%if %mdkversion < 200900
%postun client
%{clean_menus}
%endif

%files server
%defattr (-,root,root)
%doc quasar_install-1.4.7.pdf 
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/backup
%dir %{_localstatedir}/lib/%{name}/data
%dir %{_localstatedir}/lib/%{name}/data/companies
%dir %{_localstatedir}/lib/%{name}/databases
%dir %{_libdir}/%{name}/drivers
%dir %{_datadir}/%{name}/setup
%dir %{_logdir}/%{name}
%{_sbindir}/quasard
%{_sbindir}/quasar_clientd
%{_sbindir}/quasar_import
%{_sbindir}/quasar_report

%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/server.cfg
%config(noreplace) %{_sysconfdir}/%{name}/firebird.cfg
%config(noreplace) %{_sysconfdir}/%{name}/postgresql.cfg
%config(noreplace) %{_sysconfdir}/xinetd.d/quasar
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-server

%{_localstatedir}/lib/%{name}/data/cheque_fmts
%{_localstatedir}/lib/%{name}/data/handheld
%{_localstatedir}/lib/%{name}/data/models
%{_localstatedir}/lib/%{name}/data/reports
%{_localstatedir}/lib/%{name}/data/screens
%{_localstatedir}/lib/%{name}/data/shelf_labels
%{_libdir}/%{name}/drivers/libfirebird_driver.so
%{_libdir}/%{name}/drivers/libpostgresql_driver.so
%{_localstatedir}/lib/%{name}/import
%{_datadir}/%{name}/setup/quasar_setup.xpm

%files client
%defattr (-,root,root)
%doc quasar_guide-1.4.7.pdf
%dir %{_datadir}/%name/locales
%dir %{_datadir}/%{name}/locales/en_CA
%dir %{_datadir}/%{name}/locales/en_CA/help
%dir %{_datadir}/%{name}/locales/en_CA/help/images
%dir %{_datadir}/%{name}/setup
%{_bindir}/quasar
%{_bindir}/quasar_setup
%{_sbindir}/quasar_setup
%{_datadir}/applications/mandriva-%{name}-setup.desktop
%{_datadir}/applications/mandriva-%{name}.desktop

%config(noreplace) %{_sysconfdir}/%{name}/client.cfg
%config(noreplace) %{_sysconfdir}/pam.d/%{name}_setup
%{_datadir}/%{name}/locales/en_CA/messages.qm
%{_datadir}/%{name}/locales/en_CA/messages.ts
%{_datadir}/%{name}/locales/en_CA/help/*.html
%{_datadir}/%{name}/locales/en_CA/help/images/*.png
%{_datadir}/%{name}/setup/quasar_client.xpm
%{_datadir}/%{name}/setup/quasar_setup.xpm

%files doc
%defattr (-,root,root)
%doc Readme.txt Release_*.txt 
%doc quasar_reference-1.4.7.pdf quasar_features-1.4.7.pdf

