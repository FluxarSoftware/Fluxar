extern crate winreg;

use std::io;

use winreg::enums::*;
use winreg::RegKey;

pub fn setup() -> io::Result<()> {
    // Add CortexScript installation directory to the system PATH
    let cortex_script_path = std::env::current_dir()?.parent().unwrap();
    let path_var: String = format!("{};{}", cortex_script_path.to_str().unwrap(), std::env::var("PATH").unwrap());
    std::env::set_var("PATH", &path_var);

    // Register the .fsc file extension
    let hkcu: RegKey = RegKey::predef(HKEY_CURRENT_USER);
    let ext_key: (RegKey, RegDisposition) = hkcu.create_subkey("Software\\Classes\\.fsc")?;
    ext_key.set_value("", &"FSCFileType")?;

    let fsc_key: (RegKey, RegDisposition) = hkcu.create_subkey("Software\\Classes\\FSCFileType")?;
    fsc_key.set_value("", &"Fluxar Script")?;

    let icon_key = fsc_key.create_subkey("DefaultIcon")?;
    icon_key.set_value("", &"C:\\Projects\\Fluxar\\dist\\icons\\icon96.png")?;

    Ok(())
}

fn main() {
    if let Err(err) = setup() {
        eprintln!("Error setting up Fluxar: {}", err);
    } else {
        println!("Fluxar setup complete.");
    }
}
