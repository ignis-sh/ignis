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

      fileSetForCrate = crates:
        lib.fileset.toSource {
          root = ./.;
          fileset = lib.fileset.unions ([
              ./Cargo.toml
              ./Cargo.lock
              (craneLib.fileset.commonCargoSources ./crates/ignis_events)
            ]
            ++ map (crate: craneLib.fileset.commonCargoSources crate) crates);
        };

      _commonArgs = {
        inherit src;
        version = "0.1.0";
        strictDeps = true;

        buildInputs = with pkgs; [
          glib
          gdk-pixbuf
        ];

        nativeBuildInputs = with pkgs; [
          pkg-config
          python314
        ];

        doCheck = false;
      };

      cargoArtifacts = craneLib.buildDepsOnly _commonArgs;

      individualCrateArgs =
        _commonArgs
        // {
          inherit cargoArtifacts;
        };

      _mkWheelPkg = {
        pname,
        python,
        version,
        crate_name,
        crates,
      }:
        (craneLib.buildPackage (
          individualCrateArgs
          // {
            inherit pname version;
            cargoExtraArgs = "-p ${crate_name}";
            src = fileSetForCrate crates;
          }
        )).overrideAttrs (old: {
          nativeBuildInputs = old.nativeBuildInputs ++ [pkgs.maturin python];

          buildPhase = ''
            maturin build --offline --target-dir ./target --manifest-path crates/${crate_name}/Cargo.toml
          '';

          installPhase = ''
            mkdir $out
            cp target/wheels/*.whl $out/
          '';
        });

      mkPythonPkg = {
        pname,
        version,
        crate_name,
        crates,
        python,
        ps,
      }:
        ps.buildPythonPackage {
          inherit pname version;
          format = "wheel";
          src = _mkWheelPkg {inherit pname version crate_name crates python;};
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
        crates = [./crates/py_applications ./crates/applications];
      };

      pyNotificationsArgs = {
        pname = "ignis-notifications";
        crate_name = "py_notifications";
        version = "0.1.0";
        crates = [./crates/py_notifications ./crates/notifications];
      };
    in {
      ignis = pkgs.callPackage ./nix {
        inherit version;
        ignis-gvc = ignis-gvc.packages.${system}.ignis-gvc;
      };

      default = self.packages.${system}.ignis;

      ignis-notifications-glib = pkgs.callPackage ./crates/notifications_glib {};

      python313Packages = let
        ps = pkgs.python313Packages;
        python = pkgs.python313;
      in {
        ignis-applications = mkPythonPkg {
          inherit (pyApplicationsArgs) pname crate_name version crates;
          inherit python ps;
        };

        ignis-notifications = mkPythonPkg {
          inherit (pyNotificationsArgs) pname crate_name version crates;
          inherit python ps;
        };
      };

      python314Packages = let
        ps = pkgs.python314Packages;
        python = pkgs.python314;
      in {
        ignis-applications = mkPythonPkg {
          inherit (pyApplicationsArgs) pname crate_name version crates;
          inherit python ps;
        };

        ignis-notifications = mkPythonPkg {
          inherit (pyNotificationsArgs) pname crate_name version crates;
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
