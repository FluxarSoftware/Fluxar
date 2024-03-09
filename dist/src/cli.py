import os, sys, subprocess
import dist.src.basic as basic
import pathlib, shutil

name = "Fluxar"
file_extension = "fsc"
cmd_class = "fluxar"

def main():
    help = f"""
    Usage: {cmd_class} <command> <any>
    Commands:
        setup: Automatically set ups {name} to fit your computer.
        run: Runs .{file_extension} files.
        build: Build a {name} executable.
    """
    hint = "Use help command to see all commands."
    if len(sys.argv) < 2:
        print(f"\n  {name}. {hint}")
        sys.exit(1)
    command = sys.argv[1]
    if command == 'help':
        print(help)
        sys.exit(1)
    elif command == 'run':
        if len(sys.argv) < 3:
            print(f"\n   Usage: {cmd_class} run <script>")
            sys.exit(1)
        script_file = sys.argv[2]
        result, error = basic.run('<stdin>', f'cors_run("{script_file}")')

        if error:
            print(error.as_string())
        elif result:
            if len(result.elements) == 1:
                print(repr(result.elements[0]))
            else: print(repr(result))
    elif command == 'setup':
        try:
            dir_path = pathlib.Path().resolve()
            path = rf"{dir_path}..\..\dist\shell\setup.bat"
            subprocess.run([f"{path}"], shell=True)

            restart = input(f"\n{name} - Do you want to restart the computer? (y/n): ").strip().lower()
            if restart == 'y':
                subprocess.run(['shutdown', '/r', '/t', '0'])
        except Exception as e:
            sys.stderr.write("\nFluxar - Error setting up Fluxar: {}\n".format(e))
    elif command == 'init':
        template_dir = "../project_template"

        project_name = input('Enter the project name: ')
        project_dir = os.path.join(os.getcwd(), project_name)
        try:
            shutil.copytree(template_dir, project_dir)
            print(f"Fluxar - Initialized project '{project_name}' successfully.")
        except Exception as e:
            print(f"Fluxar - Error initializing project: {e}")
    elif command == 'build':
        if len(sys.argv) < 3:
            print(f"\n   Usage: {cmd_class} build <script>")
            sys.exit(1)
        script_name = sys.argv[2]
        subprocess.run(["build.exe", script_name])
    else: print(f"\n    Unknown command: {command}.\n{hint}")

if __name__ == "__main__":
    main()
