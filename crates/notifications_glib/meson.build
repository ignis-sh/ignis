project('ignis-notifications-glib', 'rust', version: '0.1')

HEADERS = [
  'include/ignis-notifications-glib/service.h',
  'include/ignis-notifications-glib/error.h',
  'include/ignis-notifications-glib/notification.h',
  'include/ignis-notifications-glib/urgency.h',
  'include/ignis-notifications-glib/close_reason.h',
  'include/ignis-notifications-glib/action.h',
]
MAIN_HEADER_FILE = 'ignis-notifications-glib/ignis-notifications-glib.h'
NAMESPACE = 'IgnisNotificationsGLib'
GIR_DEPS = ['GObject-2.0', 'GLib-2.0', 'Gio-2.0', 'GdkPixbuf-2.0']
PKG_DEPS = ['glib-2.0', 'gobject-2.0', 'gio-2.0', 'gdk-pixbuf-2.0']

NAMESPACE_VER = NAMESPACE + '-' + meson.project_version()
LIB_NAME = 'lib' + meson.project_name() + '.so'
GIR_FILENAME = NAMESPACE_VER + '.gir'
TYPELIB_FILENAME = NAMESPACE_VER + '.typelib'

foreach dep_name : PKG_DEPS
  dependency(dep_name)
endforeach

pkgconfig = import('pkgconfig')
cargo = find_program('cargo')
gir_scanner = find_program('g-ir-scanner')

cargo_options = []

if get_option('profile') == 'release'
  cargo_options += ['--release']
  cargo_target = 'release'
else
  cargo_target = 'debug'
endif

cargo_target_dir = meson.project_build_root() / 'cargo'

cargo_build = custom_target(
  'cargo-build',
  output: LIB_NAME,
  console: true,
  command: [
    cargo,
    'build',
    cargo_options,
    '--manifest-path', meson.project_source_root() / 'Cargo.toml',
    '--target-dir', cargo_target_dir,
    '&&',
    'cp',
    cargo_target_dir / cargo_target / LIB_NAME.replace('-', '_'),
    '@OUTPUT@',
  ],
)

gir_args = []

foreach dep : GIR_DEPS
  gir_args += ['--include', dep]
endforeach

foreach dep : PKG_DEPS
  gir_args += ['--pkg', dep]
endforeach

gir = custom_target(
  'gir',
  input: HEADERS,
  output: GIR_FILENAME,
  depends: cargo_build,
  install: true,
  install_dir: get_option('datadir') / 'gir-1.0',
  build_by_default: true,
  command: [
    gir_scanner,
    '-v',
    '--warn-all',
    '--namespace', NAMESPACE,
    '--nsversion', meson.project_version(),

    '-I', meson.project_source_root() / 'include',
    '--c-include', MAIN_HEADER_FILE,

    '--library', meson.project_name(),
    '--library-path', meson.current_build_dir(),

    gir_args,

    '--pkg-export', NAMESPACE_VER,

    '@INPUT@',
    '-o', '@OUTPUT@',
  ],
)

custom_target(
  'typelib',
  output: TYPELIB_FILENAME,
  input: gir,
  depends: gir,
  install_dir: get_option('libdir') / 'girepository-1.0',
  build_by_default: true,
  install: true,
  command: [
    'g-ir-compiler',
    '--includedir', meson.project_source_root() / 'include',
    '@INPUT@',
    '-o', '@OUTPUT@',
  ],
)

pkgconfig.generate(
  name: NAMESPACE,
  description: 'GLib/GObject wrapper for Ignis Notifications',
  version: meson.project_version(),
  requires: PKG_DEPS,
  libraries: [LIB_NAME],
)

py = import('python').find_installation()

test_env = environment()
test_env.prepend('GI_TYPELIB_PATH', meson.current_build_dir())
test_env.prepend('LD_LIBRARY_PATH', meson.current_build_dir())

test(
  'python-tests',
  find_program('dbus-run-session'),
  args: ['--', py, '-m', 'pytest', meson.current_source_dir() / 'tests'],
  env: test_env,
)
