Nix
===

Ignis provides a Home Manager module, which is the recommended way to install it on NixOS.

.. danger::
    You **must** refer to the `latest Ignis documentation <https://ignis-sh.github.io/ignis/latest/index.html>`_.

.. note::
    Don't use Home Manager?

    You can still install Ignis, see :ref:`without-hm` for details.

Adding Ignis to a flake
-----------------------

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
          inputs.nixpkgs.follows = "nixpkgs";  # recommended
        };
      };
    }

Home Manager
------------

The Home Manager module allows you to easily enable or disable optional features, manage the Ignis config directory, and much more.

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

        # Add Ignis to the Python environment (useful for LSP support)
        addToPythonEnv = true;

        # Put a config directory from your flake into ~/.config/ignis
        # NOTE: Home Manager will copy this directory to /nix/store
        # and create a symbolic link to the copy.
        configDir = ./ignis;

        # Enable dependencies required by certain services.
        # NOTE: This won't affect your NixOS system configuration.
        # For example, to use NetworkService, you must also enable
        # NetworkManager in your NixOS configuration:
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

A list of all available options can be found `here <https://github.com/ignis-sh/ignis/blob/main/nix/hm-module-doc.md>`_

A simple flake example
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

.. _without-hm:

Without Home Manager
--------------------

Don't use Home Manager, but still want to use optional features?

No problem, `default.nix <https://github.com/ignis-sh/ignis/blob/main/nix/default.nix>`_
allows to enable them using ``.override``:

.. code-block:: nix

  {
    inputs,
    pkgs,
    ...
  }: {
    environment.systemPackages = with pkgs; [
      # NOTE: If you need editor's LSP support
      # wrap with python3.withPackages additionally
      (inputs.ignis.packages.${pkgs.system}.default.override {
        enableAudioService = true;
        useDartSass = true;
        extraPackages = [
          # ...
        ];
      })
    ];
  }

For a list of all available attributes see the ``default.nix`` linked above.
