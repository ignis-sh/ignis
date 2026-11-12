{
  pythonPackages,
  rustPlatform,
  pkg-config,
  glib,
  gdk-pixbuf,
}:
pythonPackages.buildPythonPackage {
  pname = "ignis-mpris";
  version = "0.1.0";

  src = ../..;

  pyproject = true;

  cargoDeps = rustPlatform.importCargoLock {
    lockFile = ../../Cargo.lock;
  };

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
    pkg-config
  ];

  buildInputs = [
    glib
    gdk-pixbuf
  ];

  buildAndTestSubdir = "crates/py-mpris";
  doCheck = false;
}
