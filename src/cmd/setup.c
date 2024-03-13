#include <stdio.h>
#include <stdlib.h>
#include <Windows.h>

void changeEnvironmentTable(void) {
    #ifdef _WIN32
        int result = system("src\\cmd\\paths\\set_path.bat > nul 2>&1");
    #elif __linux__ || __APPLE__
        int result = system("src/cmd/paths/set_path.sh > /dev/null 2>&1");
    #else
        #error Unsupported platform
    #endif
    if (result != 0) {
        printf("\nError executing `changeEnvironmentTable` script: %d\n", result);
    }
}

void createRegistryEntry(void) {
    HKEY hKeyExt;
    if (RegCreateKeyEx(HKEY_CLASSES_ROOT, ".fsc", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKeyExt, NULL) == ERROR_SUCCESS) {
        RegSetValueEx(hKeyExt, NULL, 0, REG_SZ, (BYTE*)"Fluxar Source File", strlen("Fluxar Source File") + 1);

        HKEY hKeyIcon;
        if (RegCreateKeyEx(hKeyExt, "DefaultIcon", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKeyIcon, NULL) == ERROR_SUCCESS) {
            char exePath[MAX_PATH];
            GetModuleFileName(NULL, exePath, MAX_PATH);
            char* lastBackslash = strrchr(exePath, '\\');
            if (lastBackslash != NULL) {
                *lastBackslash = '\0';
                lastBackslash = strrchr(exePath, '\\');
                if (lastBackslash != NULL) {
                    *lastBackslash = '\0';
                }
            }
            strcat(exePath, "\\icons.dll,0");

            RegSetValueEx(hKeyIcon, NULL, 0, REG_SZ, (BYTE*)exePath, strlen(exePath) + 1);
            RegCloseKey(hKeyIcon);
        } else {
            printf("\nError creating DefaultIcon key: %lu\n", GetLastError());
        }
        RegCloseKey(hKeyExt);
    } else {
        printf("\nError creating registry entry for .fsc file extension: %lu\n", GetLastError());
    }
}

