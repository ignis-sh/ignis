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
  gvc,
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

  patchPhase = ''
    mkdir -p ./subprojects/gvc
    cp -r ${gvc}/* ./subprojects/gvc
  '';

  mesonFlags = [
    "-DCOMMITHASH=${self.rev or "dirty"}"
  ];

  #? avoid double wrapping. we manually pass args to wrapper
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=(
      "''${gappsWrapperArgs[@]}"
      --set LD_LIBRARY_PATH "$out/lib:${gtk4-layer-shell}/lib:$LD_LIBRARY_PATH"
    )
  '';

  # NOTE: For some reason Gvc-1.0.gir points to "/usr/local/lib/python3.13/site-packages/ignis/libgvc.so"
  # But it doesn't exist and GIR fails to load the shared library
  # So, we patch .gir to replace the wrong path with the correct relative one: "libgvc.so"
  # And recompile the typelib from patched GIR
  # FIXME: Maybe there is a better way to handle this?
  postInstall = ''
    sed -i "s|/usr/local/lib/python3.13/site-packages/ignis/libgvc.so|libgvc.so|" \
      $out/lib/python3.13/site-packages/ignis/Gvc-1.0.gir

    g-ir-compiler \
      $out/lib/python3.13/site-packages/ignis/Gvc-1.0.gir \
      -o $out/lib/python3.13/site-packages/ignis/Gvc-1.0.typelib
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
