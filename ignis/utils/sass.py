import shutil
import subprocess
from typing import Literal
from ignis.exceptions import SassCompilationError, SassNotFoundError
from ignis import get_temp_dir

# resolve Sass compiler paths and pick a default one
# "sass" (dart-sass) is the default,
# "grass" is an API-compatible drop-in replacement
sass_compilers = {}
for cmd in ("sass", "grass"):
    path = shutil.which(cmd)
    if path:
        sass_compilers[cmd] = path


def compile_file(path: str, compiler_path: str, extra_args: list[str]) -> str:
    compiled_css = f"{get_temp_dir()}/compiled.css"

    result = subprocess.run(
        [compiler_path, path, compiled_css, *extra_args] + extra_args,
        capture_output=True,
    )

    if result.returncode != 0:
        raise SassCompilationError(result.stderr.decode())

    with open(compiled_css) as file:
        return file.read()


def compile_string(string: str, compiler_path: str, extra_args: list[str]) -> str:
    process = subprocess.Popen(
        [compiler_path, "--stdin", *extra_args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(input=string.encode())

    if process.returncode != 0:
        raise SassCompilationError(stderr.decode())
    else:
        return stdout.decode()


def sass_compile(
    path: str | None = None,
    string: str | None = None,
    compiler: Literal["sass", "grass"] | None = None,
    extra_args: list[str] | None = None,
) -> str:
    """
    Compile a SASS/SCSS file or string.
    Requires either `Dart Sass <https://sass-lang.com/dart-sass/>`_
    or `Grass <https://github.com/connorskees/grass>`_.

    Args:
        path: The path to the SASS/SCSS file.
        string: A string with SASS/SCSS style.
        compiler: The desired Sass compiler, either ``sass`` or ``grass``.
        *extra_args: Additional arguments to pass to the Sass compiler.

    Raises:
        TypeError: If neither of the arguments is provided.
        SassNotFoundError: If no Sass compiler is available.
        SassCompilationError: If an error occurred while compiling SASS/SCSS.
    """
    if not sass_compilers:
        raise SassNotFoundError()

    if compiler and compiler not in sass_compilers:
        raise SassNotFoundError()

    if compiler:
        compiler_path = sass_compilers[compiler]
    else:
        compiler_path = next(iter(sass_compilers.values()))

    if not extra_args:
        extra_args = []

    if string:
        return compile_string(string, compiler_path, extra_args)

    elif path:
        return compile_file(path, compiler_path, extra_args)

    else:
        raise TypeError("sass_compile() requires at least one positional argument")
