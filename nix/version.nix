{self}: let
  initPy = builtins.readFile ../ignis/__init__.py;
  version = builtins.elemAt (builtins.match ".*__version__ = \"([^\"]*?)\".*" initPy) 0;
  date = builtins.substring 0 8 (self.lastModifiedDate or "19700101");
in "${version}+date=${date}_${self.shortRev or "dirty"}"
