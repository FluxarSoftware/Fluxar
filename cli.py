import sys, subprocess
import dist.basic as basic

def main():
    help = """
    Usage: cortex <command> <any>
    Commands:
        setup: Automatically set ups CortexScript to fit your computer.
        run: Runs .cors files. 
    """
    hint = "Use help command to see all commands."
    if len(sys.argv) < 2:
        print(f"CortexScript. {hint}")
        sys.exit(1)
    command = sys.argv[1]
    if command == 'help':
        print(help)
        sys.exit(1)
    elif command == 'run':
        if len(sys.argv) < 3:
            print("Usage: cortex run <script>")
            sys.exit(1)
        script_file = sys.argv[2]
        result, error = basic.run('<stdin>', f'cors.run("{script_file}")')

        if error:
            print(error.as_string())
        elif result:
            if len(result.elements) == 1:
                print(repr(result.elements[0]))
            else: print(repr(result))

    elif command == 'setup':
        setup_file = "setup.bat"
        subprocess.run([setup_file], shell=True)
    else: print(f"Unknown command: {command}.\n{hint}")

if __name__ == "__main__":
    main()
