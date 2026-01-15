#!/usr/bin/env bash
set -e

VERSION=1.0.0
ARCH=amd64
ROOT=$(pwd)
PKG="$ROOT/.pkg-deb"

uv run pyinstaller --onefile --copy-metadata imageio ./main.py --name camera-connect

rm -rf "$PKG"
mkdir -p "./out"
mkdir -p "$PKG/DEBIAN"
mkdir -p "$PKG/usr/bin"
mkdir -p "$PKG/lib/systemd/system"
mkdir -p "$PKG/etc/camera-connect"
mkdir -p "$PKG/usr/share/camera-connect"

# Config
cp packaging/deb/conffiles "$PKG/DEBIAN/conffiles"
cp packaging/deb/config.ini "$PKG/usr/share/camera-connect/config.ini"
cp packaging/deb/config.ini "$PKG/etc/camera-connect/config.ini"

# Binary
cp dist/camera-connect "$PKG/usr/bin/camera-connect"
chmod 755 "$PKG/usr/bin/camera-connect"

# Service
cp packaging/deb/camera-connect.service "$PKG/lib/systemd/system/"

# Control
sed "s/@VERSION@/$VERSION/" packaging/deb/control.in > "$PKG/DEBIAN/control"

# Scripts
cp packaging/deb/postinst "$PKG/DEBIAN/postinst"
cp packaging/deb/prerm "$PKG/DEBIAN/prerm"
chmod 755 "$PKG/DEBIAN/"*

dpkg-deb --build "$PKG" "out/camera-connect_${VERSION}_${ARCH}.deb"