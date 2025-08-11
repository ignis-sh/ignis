Nix
===

Ignis provides a Home Manager module, which is the recommended way to install Ignis on NixOS.

.. danger::
    You **must** refer to the `latest Ignis documentation <https://ignis-sh.github.io/ignis/latest/index.html>`_.

Adding to flake
---------------

First, add Ignis to your flake's inputs:

.. code-block:: nix

    {
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

        home-manager = {
          url = "github:nix-community/home-manager";
          inputs.nixpkgs.follows = "nixpkgs";
        };

        # Add Ignis here
        ignis = {
          url = "github:ignis-sh/ignis";
          inputs.nixpkgs.follows = "nixpkgs";  # you want this
        };
      };
    }

Home Manager
------------

The Home Manager module allows you to easily enable or disable optional features, symlink your Ignis config directory, and much more.

Add the module to your Home Manager configuration:

.. code-block:: nix

    # home.nix
    {inputs, pkgs, ...}: {
        imports = [inputs.ignis.homeManagerModules.default];
    }

Now you can easily configure Ignis using ``programs.ignis``:

.. code-block:: nix

    # home.nix
    {inputs, pkgs, ...}: {
      programs.ignis = {
        enable = true;

        # Make your editor's LSP work
        addToPythonEnv = true;

        # Symlink config dir from your flake to ~/.config/ignis
        configDir = ./ignis;

        # Enable dependencies required by some services.
        # NOTE: This won't affect your NixOS system configuration.
        # For example, to use NetworkService, you must enable NetworkManager
        # in your NixOS configuration using:
        #   networking.networkmanager.enable = true;
        services = {
          bluetooth.enable = true;
          recorder.enable = true;
          audio.enable = true;
          network.enable = true;
        };

        # Enable Sass support
        sass = {
          enable = true;
          useDartSass = true;
        };

        # Extra packages available at runtime
        # These can be regular packages or Python packages
        extraPackages = with pkgs; [
          hello
          python313Packages.jinja2
          python313Packages.materialyoucolor
          python313Packages.pillow
        ];
      };
    }



A simple Flake example
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: nix

    # flake.nix
    {
      inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

        home-manager = {
          url = "github:nix-community/home-manager";
          inputs.nixpkgs.follows = "nixpkgs";
        };

        ignis = {
          url = "github:ignis-sh/ignis";
          inputs.nixpkgs.follows = "nixpkgs";
        };
      };

      outputs = {
        self,
        nixpkgs,
        home-manager,
        ...
      } @ inputs: let
        system = "x86_64-linux";
      in {
        homeConfigurations = {
          "user@hostname" = home-manager.lib.homeManagerConfiguration {
            pkgs = nixpkgs.legacyPackages.${system};
            # Make "inputs" accessible in home.nix
            extraSpecialArgs = {inherit inputs;};
            modules = [
              ./path/to/home.nix
            ];
          };
        };
      };
    }
