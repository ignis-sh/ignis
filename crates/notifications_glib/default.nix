{
  lib,
  stdenv,
  rustPlatform,
  cargo,
  meson,
  ninja,
  pkg-config,
  rustc,
  wrapGAppsHook4,
  gobject-introspection,
  glib,
  dbus,
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "ignis-notifications-glib";
  version = "0.1";

  src = ../..;

  cargoDeps = rustPlatform.fetchCargoVendor {
    inherit (finalAttrs) src;
    name = "ignis-notifications-${finalAttrs.version}";
    hash = "sha256-ixE9RNm6/9ylQLJ/IwFcAJoAxcXbteO5qB862F0mbXM=";
  };

  nativeBuildInputs = [
    cargo
    meson
    ninja
    pkg-config
    rustc
    gobject-introspection
    rustPlatform.cargoSetupHook
    wrapGAppsHook4
  ];

  buildInputs = [
    dbus
    glib
  ];

  mesonFlags = [
    "crates/notifications_glib"
  ];

  meta = {
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
})
