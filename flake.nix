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

      fileSetForCrate = crate:
        lib.fileset.toSource {
          root = ./.;
          fileset = lib.fileset.unions [
            ./Cargo.toml
            ./Cargo.lock
            (craneLib.fileset.commonCargoSources ./crates/applications)
            (craneLib.fileset.commonCargoSources ./crates/ignis_events)
            (craneLib.fileset.commonCargoSources ./crates/notifications)
            (craneLib.fileset.commonCargoSources ./crates/py_notifications)
            (craneLib.fileset.commonCargoSources ./crates/py_applications)
            (craneLib.fileset.commonCargoSources crate)
          ];
        };

      mkWheelPkg = python: pname: crate_name: let
        commonArgs = {
          inherit src;
          strictDeps = true;

          buildInputs = with pkgs; [
            glib
            gdk-pixbuf
          ];

          nativeBuildInputs = with pkgs; [
            pkg-config
            python
          ];
        };

        cargoArtifacts = craneLib.buildDepsOnly commonArgs;

        individualCrateArgs =
          commonArgs
          // {
            inherit cargoArtifacts;
            # inherit (craneLib.crateNameFromCargoToml {inherit src;}) version;
            doCheck = false;
          };
      in
        (craneLib.buildPackage (
          individualCrateArgs
          // {
            inherit pname;
            cargoExtraArgs = "-p ${crate_name}";
            src = fileSetForCrate ./crates/${crate_name};
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

      mkPyPkgFromWheel = ps: pname: version: wheel:
        ps.buildPythonPackage {
          inherit pname version;
          format = "wheel";
          src = wheel;
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
    in {
      ignis = pkgs.callPackage ./nix {
        inherit version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };
      default = self.packages.${system}.ignis;

      ignis-notifications-glib = pkgs.callPackage ./crates/notifications_glib {};

      python313Packages = {
        ignis-applications =
          mkPyPkgFromWheel
          pkgs.python313Packages "ignis-applications" "0.1.0"
          (mkWheelPkg
            pkgs.python313 "ignis-applications" "py_applications");

        ignis-notifications =
          mkPyPkgFromWheel
          pkgs.python313Packages "ignis-notifications" "0.1.0"
          (mkWheelPkg
            pkgs.python313 "ignis-notifications" "py_notifications");
      };

      python314Packages = {
        ignis-applications =
          mkPyPkgFromWheel
          pkgs.python314Packages "ignis-applications" "0.1.0"
          (mkWheelPkg
            pkgs.python314 "ignis-applications" "py_applications");

        ignis-notifications =
          mkPyPkgFromWheel
          pkgs.python314Packages "ignis-notifications" "0.1.0"
          (mkWheelPkg
            pkgs.python314 "ignis-notifications" "py_notifications");
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
