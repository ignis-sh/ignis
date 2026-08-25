{
  description = "A widget framework for building desktop shells, written and configurable in Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    ignis-gvc = {
      url = "github:ignis-sh/ignis-gvc";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    ignis-gvc,
    rust-overlay,
    ...
  }: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = nixpkgs.lib.genAttrs systems;
    version = import ./nix/version.nix {inherit self;};

    overlays = [
      rust-overlay.overlays.default
    ];

    mkPythonPkg = pkgs: pythonPackages: path:
      pkgs.callPackage path {
        inherit pythonPackages;
      };
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
    in {
      ignis = pkgs.callPackage ./nix {
        inherit version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };
      default = self.packages.${system}.ignis;

      ignis-notifications-glib = pkgs.callPackage ./crates/notifications_glib {};

      python313Packages.ignis-applications =
        mkPythonPkg
        pkgs
        pkgs.python313Packages
        ./crates/py_applications;

      python314Packages.ignis-applications =
        mkPythonPkg
        pkgs
        pkgs.python314Packages
        ./crates/py_applications;

      pydoc = let
        pythonInventory = pkgs.fetchurl {
          url = "https://docs.python.org/3/objects.inv";
          hash = "sha256-2ykXFuFg85etBRkuKyQUDGj9VVspjhLfnvxwWtYqACQ=";
        };
      in
        pkgs.runCommand "pydoc" {
          src = ./.;
          nativeBuildInputs = with pkgs; [
            self.packages.${system}.python314Packages.ignis-applications

            python314Packages.mkdocs
            python314Packages.mkdocstrings
            python314Packages.mkdocstrings-python
            python314Packages.mkdocs-material
          ];
        } ''
          export HOME="$TMPDIR/home"
          mkdir -p "$HOME"
          cp -r "$src/pydoc" ./pydoc
          chmod -R +w ./pydoc

          substituteInPlace ./pydoc/mkdocs.yml \
                  --replace-fail \
                  "https://docs.python.org/3/objects.inv" \
                  "file://${pythonInventory}"

          cd ./pydoc

          mkdocs build --strict --site-dir $out
        '';
    });

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);

    devShells = forAllSystems (system:
      import ./nix/devshell.nix {
        inherit self;
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      });

    overlays.default = final: prev: {inherit (self.packages.${prev.system}) ignis;};

    homeManagerModules = {
      ignis = import ./nix/hm-module.nix {inherit self ignis-gvc;};
      default = self.homeManagerModules.ignis;
    };
  };
}
