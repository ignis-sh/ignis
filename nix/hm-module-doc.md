# NixOS Module Options


## [`options.programs.ignis.enable`](#L15)

Enable the Ignis widget framework

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.package`](#L17)

The Ignis package to use

**Type:** `lib.types.package`

**Default:** `self.packages.${pkgs.stdenv.hostPlatform.system}.default`

## [`options.programs.ignis.finalPackage`](#L24)

The final package after applying module modifications

**Type:** `lib.types.package`

## [`options.programs.ignis.addToPythonEnv`](#L30)


Wrap the package with python3.withPackages to include it in the global Python environment


**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.configDir`](#L34)

The config directory to use

**Type:** `with lib.types; nullOr path`

**Default:** `null`

**Example:** `./ignis`

## [`options.programs.ignis.services.audio.enable`](#L43)

Enable Audio service

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.services.network.enable`](#L46)

Enable Network service

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.services.recorder.enable`](#L49)

Enable Recorder service

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.services.bluetooth.enable`](#L52)

Enable Bluetooth service

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.sass.enable`](#L57)

Enable Sass compilation support

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.sass.useDartSass`](#L58)

Use dart-sass for Sass compilation (you probably want this)

**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.sass.useGrassSass`](#L59)


Use grass-sass for Sass compilation.
NOTE: You can set both useDartSass and useGrassSass to true. In this case, both compilers will be available.


**Type:** `boolean`

**Default:** `false`

**Example:** `true`

## [`options.programs.ignis.extraPackages`](#L65)


Extra packages to add to the PATH.
This is useful for adding additional Python packages that are needed by your config.


**Type:** `with lib.types; listOf package`

**Default:** `[]`

**Example:** `[pkgs.python313Packages.jinja2]`

---
*Generated with [nix-options-doc](https://github.com/Thunderbottom/nix-options-doc)*
