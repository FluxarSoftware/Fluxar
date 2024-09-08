#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "setup.h"

#ifdef _WIN32
#include <Windows.h>
#include <Shlwapi.h> // For PathRemoveFileSpec
#pragma comment(lib, "Shlwapi.lib")
#define DLL_EXPORT __declspec(dllexport)
#else
#include <unistd.h>
#include <dlfcn.h>
#include <limits.h>
#include <libgen.h>
#define DLL_EXPORT __attribute__((visibility("default")))
#endif

DLL_EXPORT void start();
bool IsAdmin() {
    #ifdef _WIN32
        char command[] = "net session > nul 2>&1";
        int result = system(command);
        return (result == 0);
    #else
        return (getuid() == 0);
    #endif
}
void printProgressBar(int progress, const char *message) {
    int barWidth = 45;
    int pos = barWidth * progress / 100;
    if (!IsAdmin()) {
        const char* text = "Please, make sure that you've run setup like that: `sudo ./fluxar setup`";
        #ifdef _WIN32
            text = "Please, make sure that you've run `cmd` as Administrator.";
        #endif
        printf("\033[31mSetup Error: This program must be run with administrative privileges.\033[0m\n%s", text);
        exit(1);
    } else {
        printf(""); // Placeholder to avoid color issues
    }
    #ifdef _WIN32
        for (int i = 0; i < barWidth; ++i) {
            (i < pos) ? printf(ANSI_COLOR_GREEN "-") : ( (i == pos) ? printf(ANSI_COLOR_YELLOW "-") : printf(ANSI_COLOR_RED "-") );
        }
        printf("ANSI_COLOR_RESET %d%% %s", progress, message);
    #else
        for (int i = 0; i < barWidth; ++i) {
            printf((i < pos) ? "\033[32m-" : (i == pos) ? "\033[33m-" : "\033[31m-");
        }
        printf("\033[0m %d%% %s\r", progress, message);
    #endif
    fflush(stdout);
}
void delay(int milliseconds) {
    #ifdef _WIN32
        Sleep(milliseconds);
    #else
        usleep(milliseconds * 1000);
    #endif
}
void restartComputer() {
    char response;
    printf("\nDo you want to restart your computer? (Y/N): ");
    scanf(" %c", &response);
    if (response == 'Y' || response == 'y') {
        #ifdef _WIN32
            printf("Restarting computer...\n");
            system("shutdown /r /t 0");
        #else
            printf("Restarting computer...\n");
            system("sudo shutdown -r now");
        #endif
    } else {
        printf("You chose not to restart your computer.\n\033[33mSetup is successfully completed.\n");
        printf("\033[0mPlease restart your shell session, for the best result.");
    }
}
void getMainDirectory(char *outputPath, size_t size) {
    char currentPath[PATH_MAX];
    #ifdef _WIN32
        GetModuleFileName(NULL, currentPath, sizeof(currentPath));
        PathRemoveFileSpec(currentPath);
        PathRemoveFileSpec(currentPath);
    #elif __APPLE__
        uint32_t pathSize = PATH_MAX;
        if (_NSGetExecutablePath(currentPath, &pathSize) != 0) {
            fprintf(stderr, "Error getting executable path.\n");
            exit(EXIT_FAILURE);
        }
        char *dir = dirname(currentPath);
        strncpy(outputPath, dir, size);
    #elif __linux__
        ssize_t count = readlink("/proc/self/exe", currentPath, sizeof(currentPath));
        if (count == -1) {
            perror("Error getting executable path");
            exit(EXIT_FAILURE);
        }
        currentPath[count] = '\0';
        char *dir = dirname(currentPath);
        strncpy(outputPath, dir, size);
    #else
        #error "Unsupported platform"
    #endif
}
void changeEnvironmentTable(void) {
    #ifdef _WIN32
        // result = system("src\\cmd\\paths\\setup.bat > nul 2>&1");
    #elif __linux__ || __APPLE__
        char mainDirectory[PATH_MAX];
        getMainDirectory(mainDirectory, sizeof(mainDirectory));

        const char *filePath = "/etc/paths";
        FILE *file = fopen(filePath, "a");
        if (file == NULL) {
            perror("Error opening /etc/paths");
            exit(EXIT_FAILURE);
        }
        fprintf(file, "%s\n", mainDirectory);
        fclose(file);
    #else
        #error Unsupported platform
    #endif
}
void createRegistryEntry(void) {
    #ifdef _WIN32
        HKEY hKeyExt;
        if (RegCreateKeyEx(HKEY_CLASSES_ROOT, ".fsc", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKeyExt, NULL) == ERROR_SUCCESS) {
            RegSetValueEx(hKeyExt, NULL, 0, REG_SZ, (BYTE*)"Fluxar Source File", strlen("Fluxar Source File") + 1);

            HKEY hKeyIcon;
            if (RegCreateKeyEx(hKeyExt, "DefaultIcon", 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKeyIcon, NULL) == ERROR_SUCCESS) {
                char exePath[MAX_PATH];
                GetModuleFileName(NULL, exePath, MAX_PATH);
                PathRemoveFileSpec(exePath);
                strcat(exePath, "\\icons.dll,0");

                RegSetValueEx(hKeyIcon, NULL, 0, REG_SZ, (BYTE*)exePath, strlen(exePath) + 1);
                RegCloseKey(hKeyIcon);
            } else {
                printf("\nError creating DefaultIcon key: %lu\n", GetLastError());
                exit(1); // Stop execution if there's an error
            }
            RegCloseKey(hKeyExt);
        } else {
            printf("\nError creating registry entry for .fsc file extension: %lu\n", GetLastError());
            exit(1); // Stop execution if there's an error
        }
    #elif __APPLE__
        char command[1024];
        const char *plistPath = "./com.extension.Fluxar.plist";
        printf("Command: sudo defaults import %s\n", plistPath);
        int result = system("sudo defaults import ./com.extension.Fluxar.plist");
        if (result != 0) {
            printf("Error setting UTIInfo: %d\n", result);
            exit(1);
        }
    #else
        printf("\n\033[31mThis platform does not support registry or file association setup.\033[0mn\n");
    #endif
}
void start() {
    struct Task {
        const char *message;
        int startProgress;
        int endProgress;
        void (*taskFunction)(void);
    };
    struct Task tasks[] = {
        {"- Setting up environment...", 0, 100, NULL},
        {"- Setting Directory Paths...", 0, 100, changeEnvironmentTable},
        {"- Setting file association...", 0, 100, createRegistryEntry},
        {"- Finalizing setup...", 0, 100, NULL}
    };
    int numTasks = sizeof(tasks) / sizeof(tasks[0]);
    for (int i = 0; i < numTasks; i++) {
        const char *message = tasks[i].message;
        int startProgress = tasks[i].startProgress;
        int endProgress = tasks[i].endProgress;
        void (*taskFunction)(void) = tasks[i].taskFunction;

        for (int progress = startProgress; progress <= endProgress; progress++) {
            printProgressBar(progress, message);
            if (progress % 100 == 1 && taskFunction != NULL) {
                taskFunction();  // Call the task function at 100% progress
                if (i == 1 && progress == endProgress && !IsAdmin()) {
                    printProgressBar(progress, "Error: Administrative privileges required.");
                    exit(1);
                }
            }
            delay(30);
        }
        if (taskFunction != NULL && !IsAdmin()) {
            printProgressBar(100, "Setup failed due to lack of administrative privileges.");
            exit(1);
        }
    }
    restartComputer();
}
int main() {
    return 0;
}