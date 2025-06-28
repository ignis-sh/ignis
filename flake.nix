{
  description = "A widget framework for building desktop shells, written and configurable in Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    systems.url = "github:nix-systems/default-linux";

    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };

    gvc = {
      url = "github:ignis-sh/libgnome-volume-control-wheel";
      flake = false; 
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      gvc,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        version = import ./nix/version.nix { inherit self; };
        serviceDependencies = [
          pkgs.dart-sass
          pkgs.gpu-screen-recorder
          pkgs.libpulseaudio
          pkgs.gnome-bluetooth
        ];
      in
      {
        packages = rec {
          ignis = (pkgs.callPackage ./nix { inherit self gvc version; }).override {
            serviceDependencies = serviceDependencies;
          };
          default = ignis;
        };
        apps = rec {
          ignis = (flake-utils.lib.mkApp { drv = self.packages.${system}.ignis; }).override {
            serviceDependencies = serviceDependencies;
          };
          default = ignis;
        };
      }
    )
    // {
      nixosModules.ignis = import ./nix/nixosModule.nix;
    };
}
