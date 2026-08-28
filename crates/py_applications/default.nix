{
  pythonPackages,
  rustPlatform,
}:
pythonPackages.buildPythonPackage {
  pname = "py-ignis-applications";
  version = "0.1.0";

  src = ../..;

  pyproject = true;

  cargoDeps = rustPlatform.importCargoLock {
    lockFile = ../../Cargo.lock;
  };

  nativeBuildInputs = with rustPlatform; [
    cargoSetupHook
    maturinBuildHook
  ];

  buildAndTestSubdir = "crates/py_applications";
  doCheck = false;
}
