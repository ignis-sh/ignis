{
  self,
  ignis-gvc,
}: {
  lib,
  pkgs,
  config,
  ...
}: let
  cfg = config.programs.ignis;

  ignisGvcPackage = ignis-gvc.packages.${pkgs.stdenv.hostPlatform.system}.ignis-gvc;
in {
  options.programs.ignis = {
    enable = lib.mkEnableOption "Enable the Ignis widget framework";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      defaultText = lib.literalExpression "inputs.ignis.packages.${pkgs.stdenv.hostPlatform.system}.default";
      description = "The Ignis package to use";
    };

    addToPythonEnv = lib.mkEnableOption ''
      Wrap the package with python3.withPackages to include it in the global Python environment
    '';

    configDir = lib.mkOption {
      type = with lib.types; nullOr path;
      default = null;
      example = lib.literalExpression "./ignis";
      description = "The config directory to use";
    };

    services = {
      audio = {
        enable = lib.mkEnableOption "Enable Audio service";
      };
      network = {
        enable = lib.mkEnableOption "Enable Network service";
      };
      recorder = {
        enable = lib.mkEnableOption "Enable Recorder service";
      };
      bluetooth = {
        enable = lib.mkEnableOption "Enable Bluetooth service";
      };
    };

    sass = {
      enable = lib.mkEnableOption "Enable Sass compilation support";
      useDartSass = lib.mkEnableOption "Use dart-sass for Sass compilation (you probably want this)";
      useGrassSass = lib.mkEnableOption ''
        Use grass-sass for Sass compilation.
        NOTE: You can set both useDartSass and useGrassSass to true. In this case, both compilers will be available.
      '';
    };

    extraPackages = lib.mkOption {
      type = with lib.types; listOf package;
      default = [];
      example = [pkgs.python313Packages.jinja2];
      description = ''
        Extra packages to add to the PATH.
        This is useful for adding additional Python packages that are needed by your config.
      '';
    };
  };

  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      (lib.mkIf (cfg.configDir != null) {
        xdg.configFile."ignis".source = cfg.configDir;
      })
      (let
        pkg = (cfg.package.overrideAttrs
          (
            final: prev: {
              preFixup =
                prev.preFixup
                + lib.optionalString cfg.services.audio.enable ''
                  makeWrapperArgs+=(
                    --set GI_TYPELIB_PATH "$out/lib:${ignisGvcPackage}/lib/ignis-gvc:$GI_TYPELIB_PATH"
                  )
                '';
            }
          )).override {
          extraPackages =
            cfg.extraPackages
            ++ lib.optionals cfg.services.bluetooth.enable [pkgs.gnome-bluetooth]
            ++ lib.optionals cfg.services.recorder.enable [pkgs.gpu-screen-recorder]
            ++ lib.optionals cfg.services.audio.enable [ignisGvcPackage]
            ++ lib.optionals cfg.services.network.enable [pkgs.networkmanager]
            ++ lib.optionals cfg.sass.enable (
              lib.optional cfg.sass.useDartSass pkgs.dart-sass
              ++ lib.optional cfg.sass.useGrassSass pkgs.grass-sass
            );
        };
      in {
        home.packages = [
          (
            if cfg.addToPythonEnv
            then (pkgs.python3.withPackages (_: [pkg]))
            else pkg
          )
        ];
      })
    ]
  );
}
