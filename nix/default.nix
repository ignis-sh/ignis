{
  lib,
  wrapGAppsHook4,
  glib,
  gtk4,
  gtk4-layer-shell,
  gobject-introspection,
  librsvg,
  dart-sass,
  pipewire,
  networkmanager,
  gnome-bluetooth,
  python313Packages,
  gpu-screen-recorder,
  ignis-gvc,
  extraPackages ? [],
  version ? "git",
}:
python313Packages.buildPythonPackage {
  inherit version;
  pname = "ignis";
  src = ./..;

  pyproject = true;
  build-system = [python313Packages.hatchling python313Packages.hatch-vcs];

  nativeBuildInputs = [gobject-introspection wrapGAppsHook4];

  dependencies =
    extraPackages
    ++ [
      glib
      gtk4
      ignis-gvc
      gtk4-layer-shell
      gobject-introspection
      dart-sass
      gpu-screen-recorder
      librsvg
      pipewire
      networkmanager
      gnome-bluetooth

      python313Packages.pygobject3
      python313Packages.pycairo
      python313Packages.click
      python313Packages.loguru
      python313Packages.rich
    ];

  # avoid double wrapping. we manually pass args to wrapper
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=(
      "''${gappsWrapperArgs[@]}"
      --set LD_LIBRARY_PATH "$out/lib:${gtk4-layer-shell}/lib:$LD_LIBRARY_PATH"
      --set GI_TYPELIB_PATH "$out/lib:${ignis-gvc}/lib/ignis-gvc:$GI_TYPELIB_PATH"
    )
  '';

  meta = with lib; {
    description = "A widget framework for building desktop shells, written and configurable in Python.";
    homepage = "https://github.com/ignis-sh/ignis";
    changelog = "https://github.com/ignis-sh/ignis/releases";
    license = licenses.lgpl21Plus;
    platforms = platforms.linux;
    maintainers = [];
    mainProgram = "ignis";
  };
}
