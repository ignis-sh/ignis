{
  inputs,
  lib,
  pkgs,
  config,
  ...
}:
let
  cfg = config.programs.ignis;
in
{
  options.programs.ignis = {
    enable = lib.mkEnableOption "Enable the Ignis widget framework";
    services = {
      bluetooth = lib.mkEnableOption "Enable Bluetooth service";
      upower = lib.mkEnableOption "Enable UPower service";
      recorder = lib.mkEnableOption "Enable Recorder service";
      network = lib.mkEnableOption "Enable Network service";
      audio = lib.mkEnableOption "Enable Audio service";
    };
    enableSassCompilation = lib.mkEnableOption "Enable Sass compilation support";
    extraPackages = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      example = [ pkgs.python312Packages.psutil ];
      description = ''
        Extra packages to be added to the PATH.
        This is useful for adding python packages that are needed by ignis
      '';
    };
  };

  config = lib.mkIf cfg.enable (
    let
      ignis =
        (inputs.ignis.packages.${pkgs.stdenv.hostPlatform.system}.ignis.overrideAttrs (
          final: prev: {
            mesonFlags = prev.mesonFlags ++ lib.optionals (!cfg.services.audio) [ "-Dbuild_gvc=false" ];
          }
        )).override
          {
            extraPackages = cfg.extraPackages;
            serviceDependencies = lib.optionals cfg.services.bluetooth [
                pkgs.gnome-bluetooth
              ]
              ++ lib.optionals cfg.services.recorder [
                pkgs.gpu-screen-recorder
              ]
              ++ lib.optionals cfg.services.audio [ pkgs.libpulseaudio ]
              ++ lib.optionals cfg.enableSassCompilation [ pkgs.dart-sass ];
          };
    in
    {
      environment.systemPackages = [ ignis ];
      warnings = lib.optionals (cfg.services.bluetooth && !config.hardware.bluetooth.enable) [
        "To use the Ignis Bluetooth Service, enable Bluetooth in your Nix configuration by adding 'hardware.bluetooth.enable = true'."
      ] ++ lib.optionals (cfg.services.upower && !config.services.upower.enable) [
        "To use the Ignis UPower Service, enable UPower in your Nix configuration by adding 'services.upower.enable = true'."
      ] ++ lib.optionals (cfg.services.network && !config.networking.networkmanager.enable) [
        "To use the Ignis Network Service, enable Network Manager in your Nix configuration by adding 'networking.networkmanager.enable = true'."
      ] ++ lib.optionals (cfg.services.audio && !(config.services.pipewire.enable || config.services.pulseaudio.enable)) [
        ''To use the Ignis Audio Service, Pipewire or Pulseaudio should be enabled .
        - Enable Pipewire in your Nix configurationby adding 'services.pipewire.enable = true' and 'services.pipewire.pulse.enable'
        - Enable Pulseaudio in your Nix configuration by adding 'services.pulseaudio.enable = true'.''
      ];
    }
  );
}
