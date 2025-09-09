{self}: let
  version = "0.5"; # FIXME: hard-coded
  rev = self.shortRev or "dirty";
  date = builtins.substring 0 8 (self.lastModifiedDate or "19700101");
in "${version}+g${rev}.d${date}"
