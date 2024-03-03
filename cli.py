import os, sys, subprocess
import dist.basic as basic
import pathlib
import winreg

def file_extension():
    try:
        fluxar_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        os.environ["PATH"] += ";" + fluxar_path

        hkcu = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        ext_key = winreg.CreateKey(hkcu, r"Software\Classes\.fsc")
        winreg.SetValue(ext_key, None, winreg.REG_SZ, "Fluxar Source File")

        fsc_key = winreg.CreateKey(hkcu, r"Software\Classes\FluxarFile")
        winreg.SetValue(fsc_key, None, winreg.REG_SZ, "Fluxar")

        icon_key = winreg.CreateKey(fsc_key, "DefaultIcon")
        winreg.SetValue(icon_key, None, winreg.REG_SZ, r"C:\Projects\Fluxar\dist\icons\icon96.png")

        winreg.CloseKey(icon_key)
        winreg.CloseKey(fsc_key)
        winreg.CloseKey(ext_key)
        winreg.CloseKey(hkcu)

        print("File extension association successfully updated.")
    except Exception as e:
        sys.stderr.write("Error updating file extension association: {}\n".format(e))
def main():
    help = """
    Usage: flux <command> <any>
    Commands:
        setup: Automatically set ups Fluxar to fit your computer.
        run: Runs .qu files.
        build: Build a Fluxar executable.
    """
    hint = "Use help command to see all commands."
    if len(sys.argv) < 2:
        print(f"\n  Fluxar. {hint}")
        sys.exit(1)
    command = sys.argv[1]
    if command == 'help':
        print(help)
        sys.exit(1)
    elif command == 'run':
        if len(sys.argv) < 3:
            print("\n   Usage: flux run <script>")
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
            path = rf"{dir_path}\dist\shell\setup.bat"
            subprocess.run([f"{path}"], shell=True)

            file_extension()
            print("Fluxar setup complete.")
        except Exception as e:
            sys.stderr.write("Error setting up Fluxar: {}\n".format(e))
    elif command == 'build':
        if len(sys.argv) < 3:
            print("\n   Usage: flux build <script>")
            sys.exit(1)
        script_name = sys.argv[2]
        subprocess.run(["build.exe", script_name])
    else: print(f"\n    Unknown command: {command}.\n{hint}")

if __name__ == "__main__":
    main()
