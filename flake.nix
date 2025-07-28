{
  description = "A widget framework for building desktop shells, written and configurable in Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    systems.url = "github:nix-systems/default-linux";

    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };

    ignis-gvc = {
      url = "github:ignis-sh/ignis-gvc";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ignis-gvc,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};
        version = import ./nix/version.nix {inherit self;};
        ignis-gvc-pkg = ignis-gvc.packages.${system}.ignis-gvc;
      in {
        packages = rec {
          ignis = pkgs.callPackage ./nix {
            inherit self version;
            ignis-gvc = ignis-gvc-pkg;
          };
          default = ignis;
        };
        apps = rec {
          ignis = flake-utils.lib.mkApp {drv = self.packages.${system}.ignis;};
          default = ignis;
        };

        formatter = pkgs.alejandra;

        devShells = {
          default = pkgs.mkShell {
            venvDir = "./venv";
            inputsFrom = [self.packages.${system}.ignis];

            packages = with pkgs; [
              python3Packages.venvShellHook

              (python3.withPackages (
                ps:
                  with ps; [
                    python
                    ruff
                  ]
              ))
            ];

            postVenvCreation = ''
              pip install -r dev.txt
              pip install -e .
            '';

            GI_TYPELIB_PATH = "${ignis-gvc-pkg}/lib/ignis-gvc";
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [pkgs.gtk4-layer-shell];
          };
        };
      }
    )
    // {
      overlays.default = final: prev: {inherit (self.packages.${prev.system}) ignis;};
    };
}
