import os, sys, subprocess
import argparse, shutil, pathlib

import platform, ctypes
import src.lang.handler as hand

name = "Fluxar"
version = "1.0.0"
file_extension = "fsc"
cmd_class = "fluxar"

def run_script(script_file):
    result, error = hand.run('<stdin>', f'cors_run("{script_file}")')
    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))

def setup():
    system_os = platform.system()  # Renamed to avoid shadowing the os module
    dir_path = pathlib.Path().resolve()
    path = dir_path / "src" / "cmd" / "setup.dynlib"
    try:
        if system_os == "Windows":
            path = dir_path / "src" / "cmd" / "setup.dll"
        lib = ctypes.CDLL(str(path))
        lib.start.argtypes = []
        lib.start.restype = None
        lib.start()
    except Exception as e:
        sys.stderr.write("\nError setting up Fluxar: {}\n".format(e))

def init():
    template_dir = "./init_template"
    project_name = input('Enter the project name: ')
    project_dir = os.path.join(os.getcwd(), project_name)
    try:
        shutil.copytree(template_dir, project_dir)
        print(f"Initialized project '{project_name}' successfully.")
    except Exception as e: 
        print(f"Error initializing project: {e}")

def build(script_name):
    subprocess.run(["build.exe", script_name], check=True)

def main():
    parser = argparse.ArgumentParser(description=f"Usage: {cmd_class} <command> <arg>",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--version', action='store_true', help='Show the current version')
    parser.add_argument('--help', action='store_true', help='Show help information')

    parser.add_argument("command", help="Command to execute")
    parser.add_argument("arg", nargs="?", help="Argument for the command")

    args = parser.parse_args()
    if args.version:
        print(f"{name} version {version}")
        sys.exit()
    elif args.help:
        parser.print_help()
        sys.exit()

    if args.command == 'run':
        if not args.arg:
            parser.error(f"Usage: {cmd_class} run <script>")
        run_script(args.arg)
    elif args.command == 'setup':
        setup()
    elif args.command == 'init':
        init()
    elif args.command == 'build':
        if not args.arg:
            parser.error(f"Usage: {cmd_class} build <script>")
        build(args.arg)
    elif args.command == "--list-commands":
        commands = [
            "run <script>: Run a Fluxar script.",
            "setup: Setup the Fluxar environment.",
            "init: Initialize a new Fluxar project.",
            "build <script>: Build a Fluxar project.",
            "--version: Show the current version.",
            "--help: Show help information."
        ]
        print("Available commands:")
        for command in commands:
            print(f"  {command}")
    else:
        parser.error(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
