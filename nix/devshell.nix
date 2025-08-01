{
  self,
  pkgs,
  ignis-gvc,
}: {
  default = pkgs.mkShell {
    venvDir = "./venv";
    inputsFrom = [self.packages.${pkgs.system}.ignis];

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

    GI_TYPELIB_PATH = "${ignis-gvc}/lib/ignis-gvc";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [pkgs.gtk4-layer-shell];
  };
}
