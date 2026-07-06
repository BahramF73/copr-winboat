%global debug_package %{nil}
%global forgeurl https://github.com/TibixDev/WinBoat
%global commitdate %(date -u +%Y%m%d)

Name:           winboat-nightly
Version:        0.9.0
Release:        0.%{commitdate}%{?dist}
Summary:        Windows for Penguins - nightly build

License:        MIT
URL:            %{forgeurl}
Source0:        %{forgeurl}/archive/refs/heads/main.tar.gz#/WinBoat-main.tar.gz

Conflicts:      winboat
Provides:       winboat = %{version}-%{release}

ExclusiveArch:  x86_64

BuildRequires:  bash
BuildRequires:  bun
BuildRequires:  golang
BuildRequires:  git
BuildRequires:  zip
BuildRequires:  findutils
BuildRequires:  coreutils
BuildRequires:  sed
BuildRequires:  desktop-file-utils

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  pkgconfig(libusb-1.0)
BuildRequires:  systemd-devel

# Runtime deps deliberately omitted.
# WinBoat checks missing host requirements itself at runtime.

AutoReqProv:    no

%description
WinBoat is an Electron app for running Windows apps on Linux through a
containerized Windows VM and FreeRDP integration.

This package tracks the upstream main branch and installs the unpacked
Electron application under /opt/winboat.

%prep
%autosetup -n WinBoat-main

# We do not want electron-builder to generate AppImage/deb/rpm inside rpmbuild.
# Build only the unpacked Linux directory, then package it ourselves.
sed -i 's/electron-builder --linux/electron-builder --linux dir/' package.json

# Upstream build may reference a missing icons/winboat_logo.svg.
# Use the existing PNG logo instead when needed.
if grep -q 'icons/winboat_logo.svg' electron-builder.json; then
  sed -i 's#icons/winboat_logo.svg#src/renderer/public/img/winboat_logo.png#g' electron-builder.json
fi

%build
export HOME="$PWD/.home"
export XDG_CACHE_HOME="$PWD/.cache"
export npm_config_cache="$PWD/.npm-cache"
export ELECTRON_CACHE="$PWD/.cache/electron"
export ELECTRON_BUILDER_CACHE="$PWD/.cache/electron-builder"

bun install --frozen-lockfile
bun run build:linux-gs

%install
rm -rf %{buildroot}

install -d %{buildroot}/opt/winboat
cp -a dist/linux-unpacked/. %{buildroot}/opt/winboat/

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/winboat <<'EOF'
#!/usr/bin/sh
exec /opt/winboat/winboat "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/winboat

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/winboat.desktop <<'EOF'
[Desktop Entry]
Name=WinBoat Nightly
Comment=Run Windows apps on Linux
Exec=winboat %U
Terminal=false
Type=Application
Icon=winboat
Categories=Utility;Emulator;
StartupWMClass=WinBoat
EOF

install -d %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m 0644 src/renderer/public/img/winboat_logo.png \
  %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/winboat.png

desktop-file-validate %{buildroot}%{_datadir}/applications/winboat.desktop

%files
/opt/winboat
%{_bindir}/winboat
%{_datadir}/applications/winboat.desktop
%{_datadir}/icons/hicolor/256x256/apps/winboat.png

%changelog
* Mon Jul 06 2026 Bahram Farahmand <bahram.0098.bf@gmail.com> - 0.9.0-0.20260706
- Initial nightly COPR package
