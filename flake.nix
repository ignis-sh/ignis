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
        inherit version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };
      default = self.packages.${system}.ignis;
    });

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);

    devShells = forAllSystems (system:
      import ./nix/devshell.nix {
        inherit self;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
        pkgs = nixpkgs.legacyPackages.${system};
      });

    overlays.default = final: prev: {inherit (self.packages.${prev.system}) ignis;};
  };
}
