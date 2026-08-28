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
    hash = "sha256-yF88HTp8JNKs4+OKHCxJRJLLKmeoe7yDDmZbPg7Asmw=";
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
