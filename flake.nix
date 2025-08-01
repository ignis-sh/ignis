{
  description = "A widget framework for building desktop shells, written and configurable in Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    ignis-gvc = {
      url = "github:ignis-sh/ignis-gvc";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    ignis-gvc,
    ...
  }: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = nixpkgs.lib.genAttrs systems;
    version = import ./nix/version.nix {inherit self;};
  in {
    packages = forAllSystems (system: {
      ignis = nixpkgs.legacyPackages.${system}.callPackage ./nix {
        inherit self version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };
      default = self.packages.${system}.ignis;
    });

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);

    devShells = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
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

        GI_TYPELIB_PATH = "${ignis-gvc.packages.${system}.ignis-gvc}/lib/ignis-gvc";
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [pkgs.gtk4-layer-shell];
      };
    });

    overlays.default = final: prev: {inherit (self.packages.${prev.system}) ignis;};
  };
}
