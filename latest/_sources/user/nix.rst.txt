Nix
============

Installation
------------

.. warning::
    This will install the latest (git) version of Ignis.
    Please refer to the `latest documentation <https://ignis-sh.github.io/ignis/latest/index.html>`_.

Add Ignis to the flake's inputs:

.. code-block:: nix

    {
      inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
        home-manager = {
          url = "github:nix-community/home-manager";
          inputs.nixpkgs.follows = "nixpkgs";
        };
        ignis = {
          url = "github:ignis-sh/ignis";
          # ! Important to override
          # Nix will not allow overriding dependencies if the input
          # doesn't follow your system pkgs
          inputs.nixpkgs.follows = "nixpkgs";
        };
      };
    }

Then, add the following to ``nixpkgs.overlays``:

.. code-block:: nix

    ignis.overlays.default


and the following to ``environment.systemPackages`` or ``home.packages``:

.. code-block:: nix

    pkgs.ignis

Extra Dependencies
------------------

To add extra dependencies, use the ``<pkg>.override`` function and pass the ``extraPackages`` argument to it.

.. tab-set::

    .. tab-item:: configuration.nix

        .. code-block:: nix

            { config, pkgs, lib, ... }: {
              environment.systemPackages = [
                (pkgs.ignis.override {
                  extraPackages = [
                    # Add extra dependencies here
                    # For example:
                    pkgs.python313Packages.psutil
                    pkgs.python313Packages.jinja2
                    pkgs.python313Packages.pillow
                    pkgs.python313Packages.materialyoucolor
                  ];
                })
              ];
            }

    .. tab-item:: home.nix

        .. code-block:: nix

            { config, pkgs, lib, ... }: {
              home.packages = [
                (pkgs.ignis.override {
                  extraPackages = [
                    # Add extra dependencies here
                    # For example:
                    pkgs.python313Packages.psutil
                    pkgs.python313Packages.jinja2
                    pkgs.python313Packages.pillow
                    pkgs.python313Packages.materialyoucolor
                  ];
                })
              ];
            }


Tips and Tricks
---------------

Adding Ignis to System Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can make Ignis accessible to the system Python interpreter.
This is especially useful if the LSP server of your text editor is not able to find Ignis.


.. tab-set::

    .. tab-item:: home.nix

        .. code-block:: nix

          { config, pkgs, ... }: {
            home.packages = with pkgs; [
              (python3.withPackages(ps: with ps; [
                (pkgs.ignis.override {
                  extraPackages = [
                    # Add extra packages if needed
                  ];
                })
              ]))
            ];
          }


.. danger::
    You must choose only one of the described methods.
    Do not add Ignis to the system Python if you have already added it as a package.

    Otherwise, Ignis may not be able to find extra dependencies.

The basic Flake example
^^^^^^^^^^^^^^^^^^^^^^^

.. tab-set::

    .. tab-item:: flake.nix

      .. code-block:: nix

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

            outputs = { self, nixpkgs, home-manager, ignis, ... }@inputs: let
              system = "x86_64-linux";
              lib = nixpkgs.lib;
            in {
              nixosConfigurations = {
                dummy-hostname = lib.nixosSystem {
                  specialArgs = { inherit system inputs; };

                  modules = [
                    ./path/to/configuration.nix

                    home-manager.nixosModules.home-manager {
                      home-manager = {
                        extraSpecialArgs = { inherit system inputs; };
                        useGlobalPkgs = true;
                        useUserPackages = true;
                        users.yourUserName = import ./path/to/home.nix;
                      };
                    }
                  ];
                };
              };
            };
          }
