import os, sys, subprocess
import argparse, shutil, pathlib

import src.lang.handler as hand

name = "Fluxar"
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
    try:
        dir_path = pathlib.Path().resolve()
        path = dir_path / "cmd" / "setx.exe"
        subprocess.run([str(path)], check=True)
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
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("arg", nargs="?", help="Argument for the command")

    args = parser.parse_args()

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
    else:
        parser.error(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
