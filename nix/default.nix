{
  self,
  lib,
  wrapGAppsHook4,
  pkg-config,
  ninja,
  git,
  glib,
  gtk4,
  gtk4-layer-shell,
  gobject-introspection,
  librsvg,
  dart-sass,
  libpulseaudio,
  pipewire,
  networkmanager,
  gnome-bluetooth,
  python313Packages,
  gpu-screen-recorder,
  ignis-gvc,
  extraPackages ? [ ],
  version ? "git",
}:
let
  inherit (lib)
    licenses
    platforms
    ;
  inherit (python313Packages)
    buildPythonPackage
    pygobject3
    pycairo
    click
    loguru
    rich
    meson-python
    setuptools
    ;
in
buildPythonPackage {
  inherit version;
  pname = "ignis";
  src = "${self}";

  pyproject = true;
  build-system = [ meson-python ];

  nativeBuildInputs = [
    pkg-config
    setuptools
    ninja
    git
    gobject-introspection
    wrapGAppsHook4
  ];

  dependencies = extraPackages ++ [
    glib
    gtk4
    ignis-gvc
    gtk4-layer-shell
    gobject-introspection
    dart-sass
    gpu-screen-recorder
    librsvg
    libpulseaudio
    pipewire
    networkmanager
    gnome-bluetooth

    pygobject3
    pycairo
    click
    loguru
    rich
  ];

  mesonFlags = [
    "-DCOMMITHASH=${self.rev or "dirty"}"
  ];

  #? avoid double wrapping. we manually pass args to wrapper
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=(
      "''${gappsWrapperArgs[@]}"
      --set LD_LIBRARY_PATH "$out/lib:${gtk4-layer-shell}/lib:$LD_LIBRARY_PATH"
      --set GI_TYPELIB_PATH "$out/lib:${ignis-gvc}/lib/ignis-gvc:$GI_TYPELIB_PATH"
    )
  '';

  meta = {
    description = ''
      A widget framework for building desktop shells,
      written and configurable in Python.
    '';
    homepage = "https://github.com/ignis-sh/ignis";
    changelog = "https://github.com/ignis-sh/ignis/releases";
    license = licenses.lgpl21Plus;
    platforms = platforms.linux;
    maintainers = [ ];
    mainProgram = "ignis";
  };
}
