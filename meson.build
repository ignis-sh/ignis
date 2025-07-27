project(
    'ignis',
    license: 'LGPL-2.1-or-later',
    version: run_command(['tools/get_version.py'], check: true).stdout().strip(),
    default_options: ['warning_level=2', 'werror=false']
)


# Find Python installation
python = import('python').find_installation(pure: false)

# Set folders
bindir = get_option('bindir')
pylibdir = python.get_install_dir()
pkginstalldir = join_paths(pylibdir, meson.project_name())

# Dependencies
if get_option('dependency_check')
    dependency('glib-2.0')
    dependency('gobject-introspection-1.0')
    dependency('gio-2.0')
    dependency('gtk4')
    dependency('gtk4-layer-shell-0')
endif


# Do installation
install_subdir(
    'ignis',
    install_dir: pylibdir,
)

config = configuration_data()

if get_option('COMMITHASH') != ''
    commit_hash = get_option('COMMITHASH')
else
    commit_hash = run_command('git', 'rev-parse', 'HEAD', check: false).stdout().strip()
endif

config.set('COMMIT', commit_hash)
config.set('BRANCH', run_command('git', 'branch', '--show-current', check: false).stdout().strip())
config.set('COMMIT_MSG', run_command('git', 'log', '-1', '--pretty=%B', check: false).stdout().strip().replace('\\', '\\\\').replace('"', '\\"'))

if not get_option('wheel')
install_data(
    files('bin/ignis'),
    install_dir: bindir,
    install_mode: 'rwxr-xr-x',
)
endif

configure_file(
    input: 'ignis/__commit__.py.in',
    output: '__commit__.py',
    configuration: config,
    install_dir: pkginstalldir
)
