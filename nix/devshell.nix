{
  self,
  pkgs,
  ignis-gvc,
}: let
  pythonDeps = with pkgs; [
    python3Packages.venvShellHook

    (python3.withPackages (
      ps:
        with ps; [
          python
          ruff
        ]
    ))
  ];

  extraDeps = with pkgs; [
    gnome-bluetooth
    gpu-screen-recorder
    ignis-gvc
    networkmanager
    dart-sass
  ];

  rustNativeBuildInputs = with pkgs; [
    gobject-introspection
    pkg-config
  ];

  rustBuildInputs = with pkgs; [
    rust-bin.stable.latest.default
    gdk-pixbuf
    glib
    gtk4
    meson
    ninja
    libnotify
    python313Packages.pytest
    python313Packages.pygobject3
  ];
in {
  default = pkgs.mkShell {
    venvDir = "./venv";
    inputsFrom = [self.packages.${pkgs.system}.ignis];

    packages = pythonDeps ++ extraDeps;

    nativeBuildInputs = rustNativeBuildInputs;
    buildInputs = rustBuildInputs;

    postVenvCreation = ''
      pip install -r dev.txt
      pip install -e .
    '';

    GI_TYPELIB_PATH = "${ignis-gvc}/lib/ignis-gvc";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [pkgs.gtk4-layer-shell];
  };
}
