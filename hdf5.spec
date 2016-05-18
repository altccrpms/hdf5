# AltCCRPMS
%global _cc_name %{getenv:COMPILER_NAME}
%global _cc_version %{getenv:COMPILER_VERSION}
%global _cc_name_ver %{_cc_name}-%{_cc_version}
%global _mpi_name %{getenv:MPI_NAME}
%if "%{_mpi_name}" == ""
%global _with_mpi 0
%else
%global _with_mpi 1
%endif
%if 0%{?_with_mpi}
%global _mpi_version %{getenv:MPI_VERSION}
%global _mpi_name_ver %{_mpi_name}-%{_mpi_version}
%global _name_suffix -%{_cc_name}-%{_mpi_name}
%global _name_ver_suffix -%{_cc_name_ver}-%{_mpi_name_ver}
%global _prefix /opt/%{_cc_name_ver}/%{_mpi_name_ver}/%{shortname}-%{version}
%global _modulefiledir /opt/modulefiles/MPI/%{_cc_name}/%{_cc_version}/%{_mpi_name}/%{_mpi_version}/%{shortname}
%else
%global _name_suffix -%{_cc_name}
%global _name_ver_suffix -%{_cc_name_ver}
%global _prefix /opt/%{_cc_name_ver}/%{shortname}-%{version}
%global _modulefiledir /opt/modulefiles/Compiler/%{_cc_name}/%{_cc_version}/%{shortname}
%endif
%global _sysconfdir %{_prefix}/etc

# Non gcc compilers don't generate build ids
%undefine _missing_build_ids_terminate_build

%global shortname hdf5

%global macrosdir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

# Patch version?
%global snaprel %{nil}

# NOTE:  Try not to release new versions to released versions of Fedora
# You need to recompile all users of HDF5 for each version change
Name: hdf5-1.8.17%{_name_ver_suffix}
Version: 1.8.17
Release: 1%{?dist}
Summary: A general purpose library and file format for storing scientific data
License: BSD
Group: System Environment/Libraries
URL: http://www.hdfgroup.org/HDF5/

Source0: http://www.hdfgroup.org/ftp/HDF5/releases/hdf5-%{version}%{?snaprel}/src/hdf5-%{version}%{?snaprel}.tar.bz2
Source1: h5comp
# For man pages
Source2: http://ftp.us.debian.org/debian/pool/main/h/hdf5/hdf5_1.8.16+docs-8.debian.tar.xz
Source3: hdf5.module.in
Patch0: hdf5-LD_LIBRARY_PATH.patch
# Properly run MPI_Finalize() in t_pflush1
Patch1: hdf5-mpi.patch
# Fix long double conversions on ppc64le
# https://bugzilla.redhat.com/show_bug.cgi?id=1078173
Patch3: hdf5-ldouble-ppc64le.patch

BuildRequires: krb5-devel, openssl-devel, zlib-devel, time
# For patches/rpath
BuildRequires: automake
BuildRequires: libtool
# Needed for mpi tests
BuildRequires: openssh-clients

# AltCCRPMS
Requires:       environment(modules)
Provides:       %{shortname}%{_name_suffix} = %{version}-%{release}
Provides:       %{shortname}%{_name_suffix}%{?_isa} = %{version}-%{release}
Provides:       %{shortname}%{_name_ver_suffix} = %{version}-%{release}
Provides:       %{shortname}%{_name_ver_suffix}%{?_isa} = %{version}-%{release}


%description
HDF5 is a general purpose library and file format for storing scientific data.
HDF5 can store two primary objects: datasets and groups. A dataset is
essentially a multidimensional array of data elements, and a group is a
structure for organizing objects in an HDF5 file. Using these two basic
objects, one can create and store almost any kind of scientific data
structure, such as images, arrays of vectors, and structured and unstructured
grids. You can also mix and match them in HDF5 files according to your needs.


%package devel
Summary: HDF5 development files
Group: Development/Libraries
Requires: zlib-devel
%if 0%{?_with_mpi}
Requires: %{_mpi_name_ver}-%{_cc_name_ver}-devel%{?_isa}
%endif
Provides: %{shortname}%{_name_suffix}-devel = %{version}-%{release}
Provides: %{shortname}%{_name_suffix}-devel%{?_isa} = %{version}-%{release}
Provides: %{shortname}%{_name_ver_suffix}-devel = %{version}-%{release}
Provides: %{shortname}%{_name_ver_suffix}-devel%{?_isa} = %{version}-%{release}

%description devel
HDF5 development headers and libraries.


%package static
Summary: HDF5 static libraries
Group: Development/Libraries
Requires: %{name}-devel = %{version}-%{release}
%if 0%{?_with_mpi}
Requires: %{_mpi_name_ver}-%{_cc_name_ver}-devel%{?_isa}
%endif
Provides: %{shortname}%{_name_suffix}-static = %{version}-%{release}
Provides: %{shortname}%{_name_suffix}-static%{?_isa} = %{version}-%{release}
Provides: %{shortname}%{_name_ver_suffix}-static = %{version}-%{release}
Provides: %{shortname}%{_name_ver_suffix}-static%{?_isa} = %{version}-%{release}

%description static
HDF5 static libraries.


%prep
%setup -q -a 2 -n hdf5-%{version}%{?snaprel}
%patch0 -p1 -b .LD_LIBRARY_PATH
%patch1 -p1 -b .mpi
%patch3 -p1 -b .ldouble-ppc64le
# Force shared by default for compiler wrappers (bug #1266645)
sed -i -e '/^STATIC_AVAILABLE=/s/=.*/=no/' */*/h5[cf]*.in
autoreconf -f -i


%build
#Do out of tree builds
%global _configure ../configure
#Common configure options
%global configure_opts \\\
  --disable-silent-rules \\\
  --enable-fortran \\\
  --enable-fortran2003 \\\
  --enable-hl \\\
  --enable-shared \\\
%{nil}
# --enable-cxx and --enable-parallel flags are incompatible
# --with-mpe=DIR          Use MPE instrumentation [default=no]
# --enable-cxx/fortran/parallel and --enable-threadsafe flags are incompatible
mkdir build
pushd build
ln -s ../configure .
%if !0%{?_with_mpi}
#Serial build
%configure \
  %{configure_opts} \
  --enable-cxx
make
%else
#MPI builds
export CC=mpicc
export CXX=mpicxx
export F9X=mpif90
export FC=mpif90
%configure \
  %{configure_opts} \
  --enable-parallel
make
%endif
popd


%install
make -C build install DESTDIR=${RPM_BUILD_ROOT}
rm $RPM_BUILD_ROOT/%{_libdir}/*.la
#Fixup example permissions
find ${RPM_BUILD_ROOT}%{_datadir} \( -name '*.[ch]*' -o -name '*.f90' \) -exec chmod -x {} +

# Install man pages from debian
mkdir -p ${RPM_BUILD_ROOT}%{_mandir}/man1
cp -p debian/man/*.1 ${RPM_BUILD_ROOT}%{_mandir}/man1/
rm ${RPM_BUILD_ROOT}%{_mandir}/man1/h5p[cf]c.1

# AltCCRPMS
# Make the environment-modules file
mkdir -p %{buildroot}%{_modulefiledir}
# Since we're doing our own substitution here, use our own definitions.
sed -e 's#@PREFIX@#'%{_prefix}'#' -e 's#@LIB@#%{_lib}#' < %SOURCE3 > %{buildroot}%{_modulefiledir}/%{version}


%check
# t_pflush1 fails with intel/openmpi - perhaps doesn't call MPI_Finalize()
make -C build check || :


%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig


%files
%doc COPYING MANIFEST README.txt release_docs/RELEASE.txt
%doc release_docs/HISTORY*.txt
%dir %{_prefix}
%dir %{_bindir}
%dir %{_libdir}
%dir %{_mandir}
%dir %{_mandir}/man1
%{_modulefiledir}
%{_bindir}/gif2h5
%{_bindir}/h52gif
%{_bindir}/h5copy
%{_bindir}/h5debug
%{_bindir}/h5diff
%{_bindir}/h5dump
%{_bindir}/h5import
%{_bindir}/h5jam
%{_bindir}/h5ls
%{_bindir}/h5mkgrp
%{_bindir}/h5perf_serial
%{_bindir}/h5repack
%{_bindir}/h5repart
%{_bindir}/h5stat
%{_bindir}/h5unjam
%if 0%{?_with_mpi}
%{_bindir}/h5perf
%{_bindir}/ph5diff
%endif
%{_libdir}/*.so.10*
%if !0%{?_with_mpi}
%{_libdir}/libhdf5_*cpp.so.12*
%endif
%{_mandir}/man1/gif2h5.1*
%{_mandir}/man1/h52gif.1*
%{_mandir}/man1/h5copy.1*
%{_mandir}/man1/h5diff.1*
%{_mandir}/man1/h5dump.1*
%{_mandir}/man1/h5import.1*
%{_mandir}/man1/h5jam.1*
%{_mandir}/man1/h5ls.1*
%{_mandir}/man1/h5mkgrp.1*
%{_mandir}/man1/h5perf_serial.1*
%{_mandir}/man1/h5repack.1*
%{_mandir}/man1/h5repart.1*
%{_mandir}/man1/h5stat.1*
%{_mandir}/man1/h5unjam.1*

%files devel
%dir %{_includedir}
%dir %{_datadir}
%if 0%{?_with_mpi}
%{_bindir}/h5pcc*
%{_bindir}/h5pfc*
%else
%{_bindir}/h5c++*
%{_bindir}/h5cc*
%{_bindir}/h5fc*
%endif
%{_bindir}/h5redeploy
%{_includedir}/*.h
%{_includedir}/*.mod
%{_libdir}/*.so
%{_libdir}/*.settings
%{_datadir}/hdf5_examples/
%{_mandir}/man1/h5c++.1*
%{_mandir}/man1/h5cc.1*
%{_mandir}/man1/h5fc.1*
%{_mandir}/man1/h5debug.1*
%{_mandir}/man1/h5redeploy.1*

%files static
%{_libdir}/*.a


%changelog
* Fri May 13 2016 Orion Poplawski <orion@cora.nwra.com> - 1.8.17-1
- Update to 1.8.17

* Sun Mar 20 2016 Orion Poplawski <orion@cora.nwra.com> - 1.8.16-4
- Add patch to properly call MPI_Finalize() in t_pflush1

* Wed Mar 2 2016 Orion Poplawski <orion@cora.nwra.com> - 1.8.16-3
- Make hdf5-mpich-devel require mpich-devel (bug #1314091)

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.16-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Dec 22 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.16-1.1
- Use rpm-opt-hooks for dependency handling
- Fix files for mpi build

* Fri Nov 20 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.16-1
- Update to 1.8.16

* Fri Nov 20 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.15-9.patch1
- Use MPI_FORTRAN_MOD_DIR to locate MPI Fortran module
 
* Fri Sep 25 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.15-8.patch1
- Force shared by default for compiler wrappers (bug #1266645)

* Tue Sep 15 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.15-7.patch1
- Rebuild for openmpi 1.10.0

* Sat Aug 15 2015 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 1.8.15-6.patch1
- Rebuild for MPI provides

* Sun Jul 26 2015 Sandro Mani <manisandro@gmail.com> - 1.8.15-5.patch1
- Rebuild for RPM MPI Requires Provides Change

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.15-4.patch1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jun 8 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.15-3.patch1
- Update to 1.8.15-patch1

* Fri Jun 05 2015 Dan Horák <dan[at]danny.cz> - 1.8.15-2
- drop unnecessary patch, issue seems fixed with gcc5

* Sat May 16 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.15-1
- Update to 1.8.15

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1.8.14-4
- Rebuilt for GCC 5 C++11 ABI change

* Wed Mar 11 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.14-3
- Rebuild for mpich 3.1.4 soname change

* Mon Feb 16 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.14-2
- Rebuild for gcc 5 fortran module

* Tue Jan 6 2015 Orion Poplawski <orion@cora.nwra.com> - 1.8.14-1
- Update to 1.8.14

* Wed Sep 3 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.13-7
- No longer build with -O0, seems to be working

* Wed Aug 27 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.13-6
- Rebuild for openmpi Fortran ABI change

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.13-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jun 27 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.13-4
- Make build work if not building any mpi pacakges (bug #1113610)

* Fri Jun 27 2014 Marcin Juszkiewicz <mjuszkiewicz@redhat.com> - 1.8.13-3
- Drop gnu-config patches replaced by %%configure macro

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu May 15 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.13-1
- Update to 1.8.13

* Mon Mar 24 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.12-6
- Add patch to add ppc64le to config.guess (bug #1080122)

* Wed Mar 19 2014 Orion Poplawski <orion@cora.nwra.com> - 1.8.12-5
- Add patch to fix long double conversions on ppc64le (bug #1078173)
- Run autoreconf for patches and to remove rpaths

* Sat Feb 22 2014 Deji Akingunola <dakingun@gmail.com> - 1.8.12-4
- Rebuild for mpich-3.1

* Fri Jan 31 2014 Orion Poplawski <orion@cora.nwra.com> 1.8.12-4
- Fix rpm macros install dir

* Wed Jan 29 2014 Orion Poplawski <orion@cora.nwra.com> 1.8.12-3
- Fix rpm/macros.hdf5 generation (bug #1059161)

* Wed Jan 8 2014 Orion Poplawski <orion@cora.nwra.com> 1.8.12-2
- Update debian source
- Add patch for aarch64 support (bug #925545)

* Fri Dec 27 2013 Orion Poplawski <orion@cora.nwra.com> 1.8.12-1
- Update to 1.8.12

* Fri Aug 30 2013 Dan Horák <dan[at]danny.cz> - 1.8.11-6
- disable parallel tests on s390(x)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.11-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jul 20 2013 Deji Akingunola <dakingun@gmail.com> - 1.8.11-4
- Rename mpich2 sub-packages to mpich and rebuild for mpich-3.0

* Thu Jul 11 2013 Orion Poplawski <orion@cora.nwra.com> 1.8.11-3
- Rebuild for openmpi 1.7.2

* Fri Jun 7 2013 Orion Poplawski <orion@cora.nwra.com> 1.8.11-2
- Add man pages from debian (bug #971551)

* Wed May 15 2013 Orion Poplawski <orion@cora.nwra.com> 1.8.11-1
- Update to 1.8.11

* Mon Mar 11 2013 Ralf Corsépius <corsepiu@fedoraproject.org> - 1.8.10-3
- Remove %%config from %%{_sysconfdir}/rpm/macros.*
  (https://fedorahosted.org/fpc/ticket/259).

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Nov 14 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.10-1
- Update to 1.8.10
- Rebase LD_LIBRARY_PATH patch
- Drop ph5diff patch fixed upstream

* Mon Nov 12 2012 Peter Robinson <pbrobinson@fedoraproject.org> 1.8.9-5
- Enable openmpi support on ARM as we now have it

* Mon Nov 5 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.9-4
- Rebuild for fixed openmpi f90 soname

* Thu Nov 1 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.9-3
- Rebuild for openmpi and mpich2 soname bumps

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue May 15 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.9-1
- Update to 1.8.9

* Mon Feb 20 2012 Dan Horák <dan[at]danny.cz> 1.8.8-9
- use %%{mpi_list} also for tests

* Wed Feb 15 2012 Peter Robinson <pbrobinson@fedoraproject.org> - 1.8.8-8
- disable openmpi for ARM as we currently don't have it

* Fri Feb 10 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.8-7
- Add patch to fix parallel mpi tests
- Add patch to fix bug in parallel h5diff

* Sat Jan 7 2012 Orion Poplawski <orion@cora.nwra.com> 1.8.8-6
- Enable Fortran 2003 support (bug 772387)

* Wed Dec 21 2011 Dan Horák <dan[at]danny.cz> 1.8.8-5
- reintroduce the tstlite patch for ppc64 and s390x

* Thu Dec 01 2011 Caolán McNamara <caolanm@redhat.com> 1.8.8-4
- Related: rhbz#758334 hdf5 doesn't build on ppc64

* Fri Nov 25 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.8-3
- Enable static MPI builds

* Wed Nov 16 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.8-2
- Add rpm macro %%{_hdf5_version} for convenience

* Tue Nov 15 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.8-1
- Update to 1.8.8
- Drop tstlite patch
- Add patch to avoid setting LD_LIBRARY_PATH

* Wed Jun 01 2011 Karsten Hopp <karsten@redhat.com> 1.8.7-2
- drop ppc64 longdouble patch, not required anymore

* Tue May 17 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.7-1
- Update to 1.8.7

* Tue Mar 29 2011 Deji Akingunola <dakingun@gmail.com> - 1.8.6-2
- Rebuild for mpich2 soname bump

* Fri Feb 18 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.6-1
- Update to 1.8.6-1
- Update tstlite patch - not fixed yet

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.5.patch1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Feb 6 2011 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-7
- Add Requires: zlib-devel to hdf5-devel

* Sun Dec 12 2010 Dan Horák <dan[at]danny.cz> 1.8.5.patch1-6
- fully conditionalize MPI support

* Wed Dec 8 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-5
- Add EL6 compatibility - no mpich2 on ppc64

* Wed Oct 27 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-4
- Really fixup all permissions

* Wed Oct 27 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-3
- Add docs to the mpi packages
- Fixup example source file permissions

* Tue Oct 26 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-2
- Build parallel hdf5 packages for mpich2 and openmpi
- Rework multiarch support and drop multiarch patch

* Tue Sep 7 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5.patch1-1
- Update to 1.8.5-patch1

* Wed Jun 23 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5-4
- Re-add rebased tstlite patch - not fixed yet

* Wed Jun 23 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5-3
- Update longdouble patch for 1.8.5

* Wed Jun 23 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5-2
- Re-add longdouble patch on ppc64 for EPEL builds

* Mon Jun 21 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.5-1
- Update to 1.8.5
- Drop patches fixed upstream

* Mon Mar 1 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.4.patch1-1
- Update to 1.8.4-patch1

* Wed Jan 6 2010 Orion Poplawski <orion@cora.nwra.com> 1.8.4-1
- Update to 1.8.4
- Must compile with -O0 due to gcc-4.4 incompatability
- No longer need -fno-strict-aliasing

* Thu Oct 1 2009 Orion Poplawski <orion@cora.nwra.com> 1.8.3-3.snap12
- Update to 1.8.3-snap12
- Update signal patch
- Drop detect and filter-as-option patch fixed upstream
- Drop ppc only patch
- Add patch to skip tstlite test for now, problem reported upstream
- Fixup some source file permissions

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jun 2 2009 Orion Poplawski <orion@cora.nwra.com> 1.8.3-1
- Update to 1.8.3
- Update signal and detect patches
- Drop open patch fixed upstream

* Sat Apr 18 2009 Karsten Hopp <karsten@redhat.com> 1.8.2-1.1
- fix s390x builds, s390x is 64bit, s390 is 32bit

* Mon Feb 23 2009 Orion Poplawski <orion@cora.nwra.com> 1.8.2-1
- Update to 1.8.2
- Add patch to compile H5detect without optimization - make detection
  of datatype characteristics more robust - esp. long double
- Update signal patch
- Drop destdir patch fixed upstream
- Drop scaleoffset patch
- Re-add -fno-strict-aliasing
- Keep settings file needed for -showconfig (bug #481032)
- Wrapper script needs to pass arguments (bug #481032)

* Wed Oct 8 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.1-3
- Add sparc64 to 64-bit conditionals

* Fri Sep 26 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.1-2
- Add patch to filter -little as option used on sh arch (#464052)

* Thu Jun 5 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.1-1
- Update to 1.8.1

* Tue May 27 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.1-0.rc1.1
- Update to 1.8.1-rc1

* Tue May 13 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.0.snap5-2
- Use new %%{_fmoddir} macro
- Re-enable ppc64, disable failing tests.  Failing tests are for
  experimental long double support.

* Mon May 5 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.0.snap5-1
- Update to 1.8.0-snap5
- Remove --enable-threadsafe, incompatible with --enable-cxx and
  --enable-fortran
- ExcludeArch ppc64 until we can get it to build (bug #445423)

* Tue Mar 4 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.0-2
- Remove failing test for now

* Fri Feb 29 2008 Orion Poplawski <orion@cora.nwra.com> 1.8.0-1
- Update to 1.8.0, drop upstreamed patches
- Update signal patch
- Move static libraries into -static sub-package
- Make -devel multiarch (bug #341501)

* Wed Feb  6 2008 Orion Poplawski <orion@cora.nwra.com> 1.6.6-7
- Add patch to fix strict-aliasing
- Disable production mode to enable debuginfo

* Tue Feb  5 2008 Orion Poplawski <orion@cora.nwra.com> 1.6.6-6
- Add patch to fix calling free() in H5PropList.cpp

* Tue Feb  5 2008 Orion Poplawski <orion@cora.nwra.com> 1.6.6-5
- Add patch to support s390 (bug #431510)

* Mon Jan  7 2008 Orion Poplawski <orion@cora.nwra.com> 1.6.6-4
- Add patches to support sparc (bug #427651)

* Tue Dec  4 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.6-3
- Rebuild against new openssl

* Fri Nov 23 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.6-2
- Add patch to build on alpha (bug #396391)

* Wed Oct 17 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.6-1
- Update to 1.6.6, drop upstreamed patches
- Explicitly set compilers

* Fri Aug 24 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.5-9
- Update license tag to BSD
- Rebuild for BuildID

* Wed Aug  8 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.5-8
- Fix memset typo
- Pass mode to open with O_CREAT

* Mon Feb 12 2007 Orion Poplawski <orion@cora.nwra.com> 1.6.5-7
- New project URL
- Add patch to use POSIX sort key option
- Remove useless and multilib conflicting Makefiles from html docs
  (bug #228365)
- Make hdf5-devel own %%{_docdir}/%%{name}

* Tue Aug 29 2006 Orion Poplawski <orion@cora.nwra.com> 1.6.5-6
- Rebuild for FC6

* Wed Mar 15 2006 Orion Poplawski <orion@cora.nwra.com> 1.6.5-5
- Change rpath patch to not need autoconf
- Add patch for libtool on x86_64
- Fix shared lib permissions

* Mon Mar 13 2006 Orion Poplawski <orion@cora.nwra.com> 1.6.5-4
- Add patch to avoid HDF setting the compiler flags

* Mon Feb 13 2006 Orion Poplawski <orion@cora.nwra.com> 1.6.5-3
- Rebuild for gcc/glibc changes

* Wed Dec 21 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.5-2
- Don't ship h5perf with missing library

* Wed Dec 21 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.5-1
- Update to 1.6.5

* Wed Dec 21 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-9
- Rebuild

* Wed Nov 30 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-8
- Package fortran files properly
- Move compiler wrappers to devel

* Fri Nov 18 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-7
- Add patch for fortran compilation on ppc

* Wed Nov 16 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-6
- Bump for new openssl

* Tue Sep 20 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-5
- Enable fortran since the gcc bug is now fixed

* Tue Jul 05 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-4
- Make example scripts executable

* Wed Jun 29 2005 Orion Poplawski <orion@cora.nwra.com> 1.6.4-3
- Add --enable-threads --with-pthreads to configure
- Add %%check
- Add some %%docs
- Use %%makeinstall
- Add patch to fix test for h5repack
- Add patch to fix h5diff_attr.c

* Mon Jun 27 2005 Tom "spot" Callaway <tcallawa@redhat.com> 1.6.4-2
- remove szip from spec, since szip license doesn't meet Fedora standards

* Sun Apr 3 2005 Tom "spot" Callaway <tcallawa@redhat.com> 1.6.4-1
- inital package for Fedora Extras
