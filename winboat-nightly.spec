# Disable automatic debug package generation.
%global debug_package %{nil}

# Upstream repository URL.
%global forgeurl https://github.com/TibixDev/WinBoat

# Use the current UTC date as the package release suffix.
%global commitdate %(date -u +%Y%m%d%H%M)

Name:           winboat-nightly
Version:        0.9.0
Release:        0.%{commitdate}%{?dist}
Summary:        Windows for Penguins - nightly build

License:        MIT
URL:            %{forgeurl}

# Always build from the latest main branch snapshot.
Source0:        %{forgeurl}/archive/refs/heads/main.tar.gz#/WinBoat-main.tar.gz

# Prevent installation alongside other WinBoat packages.
Conflicts:      winboat

# WinBoat currently supports x86_64 only.
ExclusiveArch:  x86_64

# Basic build utilities.
BuildRequires:  bash
BuildRequires:  golang
BuildRequires:  git
BuildRequires:  findutils
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils

# Build toolchain and required development libraries.
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  pkgconfig(libusb-1.0)
BuildRequires:  systemd-devel
BuildRequires:  curl
BuildRequires:  unzip
BuildRequires:  nodejs

# Do not automatically generate runtime dependencies.
AutoReqProv:    no

%description
WinBoat is an Electron app for running Windows apps on Linux through a
containerized Windows VM and FreeRDP integration.

This package tracks the upstream main branch and installs the unpacked
Electron application under /opt/winboat.

%prep
%autosetup -n winboat-main

# Replace the missing upstream SVG icon with the available PNG icon.
if grep -q 'icons/winboat_logo.svg' electron-builder.json; then
  sed -i 's#icons/winboat_logo.svg#src/renderer/public/img/winboat_logo.png#g' electron-builder.json
fi

%build
# Install Bun locally inside the build directory.
export BUN_INSTALL="$PWD/.bun"
curl -fsSL https://bun.sh/install | bash
export PATH="$BUN_INSTALL/bin:$PATH"

# Keep build caches inside the build directory.
export HOME="$PWD/.home"
export XDG_CACHE_HOME="$PWD/.cache"
export npm_config_cache="$PWD/.npm-cache"
export ELECTRON_CACHE="$PWD/.cache/electron"
export ELECTRON_BUILDER_CACHE="$PWD/.cache/electron-builder"

bun --version

# Install all dependencies required for building.
bun install --frozen-lockfile

# Build the guest server and Electron application.
bash build-guest-server.sh
bun scripts/build.ts

# Ensure the Electron main process entry point was generated.
(cd src/main && ../../node_modules/.bin/tsc --pretty false)
test -f build/main/main.js

# Create a clean packaging directory with production dependencies only.
rm -rf pkgroot
mkdir -p pkgroot

cp package.json electron-builder.json pkgroot/
cp bun.lock* pkgroot/ 2>/dev/null || true
cp -a build pkgroot/
cp -a src pkgroot/
cp -a guest_server pkgroot/
cp -a data pkgroot/
cp -a icons pkgroot/ || true
cp -a patches pkgroot/ || true

# Install production dependencies and build the distributable archive.
cd pkgroot
bun install --frozen-lockfile --production
bun ../node_modules/.bin/electron-builder --linux tar.bz2
cd ..

# Move the generated artifacts back to the project root.
rm -rf dist
mv pkgroot/dist dist

%install
rm -rf %{buildroot}

# Extract the generated archive.
mkdir -p unpacked
tar -xjf dist/*.tar.bz2 -C unpacked

# Install the application under /opt.
install -d %{buildroot}/opt/winboat
cp -a unpacked/winboat-*-x64/. %{buildroot}/opt/winboat/

# Remove any accidental build caches.
find %{buildroot}/opt/winboat -type d -name ".cache" -exec rm -rf {} +
find %{buildroot}/opt/winboat -type d -name ".npm-cache" -exec rm -rf {} +
find %{buildroot}/opt/winboat -type d -name ".bun" -exec rm -rf {} +

# Install launcher wrapper.
install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/winboat <<'EOF'
#!/bin/sh
exec /opt/winboat/winboat "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/winboat

# Install desktop entry.
install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/winboat.desktop <<'EOF'
[Desktop Entry]
Name=WinBoat
Comment=Run Windows apps on Linux
Exec=winboat %U
Terminal=false
Type=Application
Icon=winboat
Categories=Utility;Emulator;
StartupWMClass=WinBoat
EOF

# Install application icon.
install -d %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m 0644 src/renderer/public/img/winboat_logo.png \
  %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/winboat.png

# Validate the desktop file.
desktop-file-validate %{buildroot}%{_datadir}/applications/winboat.desktop

%files
/opt/winboat
%{_bindir}/winboat
%{_datadir}/applications/winboat.desktop
%{_datadir}/icons/hicolor/256x256/apps/winboat.png

%changelog
%autochangelog