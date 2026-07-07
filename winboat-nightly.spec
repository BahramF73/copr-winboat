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
BuildRequires:  curl
BuildRequires:  unzip
BuildRequires:  nodejs

AutoReqProv:    no

%description
WinBoat is an Electron app for running Windows apps on Linux through a
containerized Windows VM and FreeRDP integration.

This package tracks the upstream main branch and installs the unpacked
Electron application under /opt/winboat.

%prep
%autosetup -n winboat-main

if grep -q 'icons/winboat_logo.svg' electron-builder.json; then
  sed -i 's#icons/winboat_logo.svg#src/renderer/public/img/winboat_logo.png#g' electron-builder.json
fi

%build
export BUN_INSTALL="$PWD/.bun"
curl -fsSL https://bun.sh/install | bash
export PATH="$BUN_INSTALL/bin:$PATH"

export HOME="$PWD/.home"
export XDG_CACHE_HOME="$PWD/.cache"
export npm_config_cache="$PWD/.npm-cache"
export ELECTRON_CACHE="$PWD/.cache/electron"
export ELECTRON_BUILDER_CACHE="$PWD/.cache/electron-builder"

bun --version
bun install --frozen-lockfile

bash build-guest-server.sh
bun scripts/build.ts

rm -rf pkgroot
mkdir -p pkgroot

cp package.json electron-builder.json pkgroot/
cp bun.lock* pkgroot/ 2>/dev/null || true
cp -a build pkgroot/
cp -a src pkgroot/
cp -a guest_server pkgroot/
cp -a data pkgroot/
cp -a icons pkgroot/ || true

cd pkgroot
bun install --frozen-lockfile --production
../node_modules/.bin/electron-builder --linux tar.bz2
cd ..

rm -rf dist
mv pkgroot/dist dist

du -sh dist/* || true
bunx --yes @electron/asar extract dist/linux-unpacked/resources/app.asar app-asar
du -h -d 3 app-asar | sort -h | tail -80

%install
rm -rf %{buildroot}

du -sh dist/* || true

mkdir -p unpacked
tar -xjf dist/*.tar.bz2 -C unpacked

install -d %{buildroot}/opt/winboat

find dist/linux-unpacked/resources -maxdepth 1 -type f -exec ls -lh {} \;
find dist/linux-unpacked/resources -type f -printf "%s %p\n" | sort -nr | head -30

find unpacked -maxdepth 3 -type f -exec ls -lh {} \; | sort -k5 -hr | head -30
find unpacked -type f -printf "%s %p\n" | sort -nr | head -30

cp -a unpacked/winboat-*-x64/. %{buildroot}/opt/winboat/

find %{buildroot}/opt/winboat -type d -name ".cache" -exec rm -rf {} +
find %{buildroot}/opt/winboat -type d -name ".npm-cache" -exec rm -rf {} +
find %{buildroot}/opt/winboat -type d -name ".bun" -exec rm -rf {} +

du -h -d 3 %{buildroot}/opt/winboat | sort -h | tail -50

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