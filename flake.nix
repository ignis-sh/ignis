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

    crane.url = "github:ipetkov/crane";
  };

  outputs = {
    self,
    nixpkgs,
    ignis-gvc,
    rust-overlay,
    crane,
    ...
  }: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = nixpkgs.lib.genAttrs systems;
    version = import ./nix/version.nix {inherit self;};

    overlays = [
      rust-overlay.overlays.default
    ];
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs {
        inherit system overlays;
      };

      inherit (pkgs) lib;

      # CRANE STUFF

      customRustToolchain = pkgs.rust-bin.nightly.latest.default;
      craneLib =
        (crane.mkLib pkgs).overrideToolchain customRustToolchain;

      src = craneLib.cleanCargoSource ./.;

      fileSetForCrate = lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./Cargo.toml
          ./Cargo.lock
          (craneLib.fileset.commonCargoSources ./crates/applications)
          (craneLib.fileset.commonCargoSources ./crates/ignis_events)
          (craneLib.fileset.commonCargoSources ./crates/notifications)
          (craneLib.fileset.commonCargoSources ./crates/py_notifications)
          (craneLib.fileset.commonCargoSources ./crates/py_applications)
        ];
      };

      _mkWheelPkg = {
        python,
        pname,
        version,
        crate_name,
      }: let
        commonArgs = {
          inherit src pname version;
          strictDeps = true;

          buildInputs = with pkgs; [
            glib
            gdk-pixbuf
          ];

          nativeBuildInputs = with pkgs; [
            pkg-config
            python
          ];

          doCheck = false;
        };

        cargoArtifacts = craneLib.buildDepsOnly commonArgs;

        individualCrateArgs =
          commonArgs
          // {
            inherit cargoArtifacts;
          };
      in
        (craneLib.buildPackage (
          individualCrateArgs
          // {
            cargoExtraArgs = "-p ${crate_name}";
            src = fileSetForCrate;
          }
        )).overrideAttrs (old: {
          nativeBuildInputs = old.nativeBuildInputs ++ [pkgs.maturin];

          buildPhase =
            old.buildPhase
            + ''
              maturin build --offline --target-dir ./target --manifest-path crates/${crate_name}/Cargo.toml
            '';

          installPhase =
            old.installPhase
            + ''
              cp target/wheels/*.whl $out/
            '';
        });

      mkPythonPkg = {
        pname,
        version,
        crate_name,
        python,
        ps,
      }:
        ps.buildPythonPackage {
          inherit pname version;
          format = "wheel";
          src = _mkWheelPkg {inherit python pname version crate_name;};
          doCheck = false;

          unpackPhase = ''
            runHook preUnpack

            wheel=$(find "$src" -maxdepth 1 -name '*.whl' -print -quit)
            if [ -z "$wheel" ]; then
              echo "error: no wheel found in $src"
              exit 1
            fi

            mkdir -p dist
            cp -r "$wheel" "dist/$(stripHash "$wheel")"
          '';
        };

      pyApplicationsArgs = {
        pname = "ignis-applications";
        crate_name = "py_applications";
        version = "0.1.0";
      };

      pyNotificationsArgs = {
        pname = "ignis-notifications";
        crate_name = "py_notifications";
        version = "0.1.0";
      };
    in {
      ignis = pkgs.callPackage ./nix {
        inherit version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };
      default = self.packages.${system}.ignis;

      ignis-notifications-glib = pkgs.callPackage ./crates/notifications_glib {};

      python313Packages = let
        python = pkgs.python313;
        ps = pkgs.python313Packages;
      in {
        ignis-applications = mkPythonPkg {
          inherit (pyApplicationsArgs) pname crate_name version;
          inherit python ps;
        };

        ignis-notifications = mkPythonPkg {
          inherit (pyNotificationsArgs) pname crate_name version;
          inherit python ps;
        };
      };

      python314Packages = let
        python = pkgs.python314;
        ps = pkgs.python314Packages;
      in {
        ignis-applications = mkPythonPkg {
          inherit (pyApplicationsArgs) pname crate_name version;
          inherit python ps;
        };

        ignis-notifications = mkPythonPkg {
          inherit (pyNotificationsArgs) pname crate_name version;
          inherit python ps;
        };
      };
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
