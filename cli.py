import os, sys, subprocess
import dist.basic as basic
import pathlib

def main():
    help = """
    Usage: quantum <command> <any>
    Commands:
        setup: Automatically set ups Quantum to fit your computer.
        run: Runs .qu files.
        build: Build a Quantum executable.
    """
    hint = "Use help command to see all commands."
    if len(sys.argv) < 2:
        print(f"\n  Quantum. {hint}")
        sys.exit(1)
    command = sys.argv[1]
    if command == 'help':
        print(help)
        sys.exit(1)
    elif command == 'run':
        if len(sys.argv) < 3:
            print("\n   Usage: quantum run <script>")
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
        dir_path = pathlib.Path().resolve()
        path = rf"{dir_path}\dist\terminal\setup.bat"
        subprocess.run([f"{path}"], shell=True)
    elif command == 'build':
        if len(sys.argv) < 3:
            print("\n   Usage: quantum build <script>")
            sys.exit(1)
        script_name = sys.argv[2]
        subprocess.run(["build.exe", script_name])
    else: print(f"\n    Unknown command: {command}.\n{hint}")

if __name__ == "__main__":
    main()
