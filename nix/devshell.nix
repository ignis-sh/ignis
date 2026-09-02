{
  self,
  pkgs,
  ignis-gvc,
}: let
  pythonDeps = with pkgs; [
    python313Packages.venvShellHook
    python313
    ruff
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
    rust-bin.nightly.latest.default
    gdk-pixbuf
    glib
    gtk4
    meson
    ninja
    libnotify
    python313Packages.pytest
    python313Packages.pygobject3
    just
    gi-docgen
    maturin
    python313Packages.mkdocs
    python313Packages.mkdocstrings
    python313Packages.mkdocstrings-python
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

  pydocbuild = pkgs.mkShell {
    packages = with pkgs; [
      self.packages.${pkgs.system}.python314Packages.ignis-applications

      python314Packages.mkdocs
      python314Packages.mkdocstrings
      python314Packages.mkdocstrings-python
      python314Packages.mkdocs-material
    ];
  };

  rustci = pkgs.mkShell {
    rustNativeBuildInputs = with pkgs; [
      gobject-introspection
      pkg-config
    ];

    buildInputs = with pkgs; [
      rust-bin.nightly.latest.default
      gdk-pixbuf
      glib
      gtk4
      meson
      ninja
      libnotify
      python313Packages.pytest
      python313Packages.pygobject3
      just
      gi-docgen
    ];
  };
}
