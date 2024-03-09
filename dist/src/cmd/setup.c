#include <stdio.h>
#include <stdlib.h>
#include <Windows.h>

void changeEnvironmentTable(void) {
    #ifdef _WIN32
        system("paths\\set_path.bat > nul 2>&1");
    #elif __linux__ || __APPLE__
        system("./paths/set_path.sh > /dev/null 2>&1");
    #else
        #error Unsupported platform
    #endif
}

void createRegistryEntry(void) {
    HKEY hKey;
    if (RegCreateKeyEx(HKEY_CLASSES_ROOT, ".fsc", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKey, NULL) == ERROR_SUCCESS) {
        RegSetValueEx(hKey, NULL, 0, REG_SZ, (BYTE*)"Fluxar Source File", strlen("Fluxar Source File") + 1);
        RegCloseKey(hKey);
    } else {
        printf("\nError creating registry entry: %lu\n", GetLastError());
    }
}
