{
  lib,
  wrapGAppsHook4,
  glib,
  gtk4,
  gtk4-layer-shell,
  gobject-introspection,
  librsvg,
  python313Packages,
  version ? "git",
  extraPackages ? [],
  enableAudioService ? false, # enable Audio Service
  ignis-gvc,
  enableNetworkService ? false, # enable Network Service
  networkmanager,
  enableRecorderService ? false, # enable Recorder Service
  gpu-screen-recorder,
  enableBluetoothService ? false, # enable Bluetooth Service
  gnome-bluetooth,
  useDartSass ? false, # Use dart-sass for Sass compilation
  dart-sass,
  useGrassSass ? false, # Use grass-sass for Sass compilation
  grass-sass,
}:
python313Packages.buildPythonPackage {
  inherit version;
  pname = "ignis";
  src = ./..;

  pyproject = true;
  build-system = [python313Packages.hatchling python313Packages.hatch-vcs];

  nativeBuildInputs = [gobject-introspection wrapGAppsHook4];

  dependencies =
    [
      glib
      gtk4
      gtk4-layer-shell
      gobject-introspection
      librsvg

      python313Packages.pygobject3
      python313Packages.pycairo
      python313Packages.click
      python313Packages.loguru
      python313Packages.rich
    ]
    ++ lib.optionals enableAudioService [ignis-gvc]
    ++ lib.optionals enableNetworkService [networkmanager]
    ++ lib.optionals enableRecorderService [gpu-screen-recorder]
    ++ lib.optionals enableBluetoothService [gnome-bluetooth]
    ++ lib.optionals useDartSass [dart-sass]
    ++ lib.optionals useGrassSass [grass-sass]
    ++ extraPackages;

  # avoid double wrapping. we manually pass args to wrapper
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=(
      "''${gappsWrapperArgs[@]}"
      --prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [gtk4-layer-shell]}
      ${lib.optionalString enableAudioService ''--prefix GI_TYPELIB_PATH : "${ignis-gvc}/lib/ignis-gvc"''}
    )
  '';

  meta = with lib; {
    description = "A widget framework for building desktop shells, written and configurable in Python.";
    homepage = "https://github.com/ignis-sh/ignis";
    changelog = "https://github.com/ignis-sh/ignis/releases";
    license = licenses.lgpl21Plus;
    platforms = platforms.linux;
    maintainers = with maintainers; [linkfrg];
    mainProgram = "ignis";
  };
}
