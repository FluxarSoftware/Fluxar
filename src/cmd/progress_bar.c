#include <stdio.h>
#include <stdlib.h>
#include <Windows.h>
#include "progress_bar.h"

void changeEnvironmentTable();
void createRegistryEntry();

typedef void (*TaskFunction)(void);

#include <stdbool.h>
bool IsAdmin() {
    char command[] = "net session > nul 2>&1";
    int result = system(command);
    return (result == 0);
}
void printProgressBar(int progress, const char *message) {
    int barWidth = 45;
    int pos = barWidth * progress / 100;

    if (!IsAdmin()) {
        printf("    Error: This program must be run with administrative privileges.\n");
        exit(1);
    } else {
      printf(""); // I did it here because somehow it makes colors in cmd with it. do not delete, it will break everything.
    }
    printf(ANSI_COLOR_GREEN "    [");
    for (int i = 0; i < barWidth; ++i) {
        (i < pos) ? printf(ANSI_COLOR_GREEN "-") : ( (i == pos) ? printf(ANSI_COLOR_YELLOW "-") : printf(ANSI_COLOR_RED "-") );
    }
    printf(ANSI_COLOR_GREEN "] %d%% %s" ANSI_COLOR_RESET "\r", progress, message);
    fflush(stdout);
}
void restartComputer() {
    printf("\nDo you want to restart your computer? (Y/N): ");
    char response;
    scanf(" %c", &response);
    if (response == 'Y' || response == 'y') {
        printf("Restarting computer...\n");
        system("shutdown /r /t 0");
    } else {
        printf("You chose not to restart your computer. Setup is successfully completed.\n");
    }
}
int main() {
    struct Task {
        const char *message;
        int startProgress;
        int endProgress;
        TaskFunction taskFunction;
    };
    TaskFunction changeEnvTable = changeEnvironmentTable;
    TaskFunction createRegEntr = createRegistryEntry;

    struct Task tasks[] = {
        {"- Setting up environment...", 0, 25, NULL},
        {"- Changing Directory Paths...", 25, 50, changeEnvTable},
        {"- Setting up the Registery Keys...", 50, 75, createRegEntr},
        {"- Doing some task...", 75, 100, NULL},
        {"- Finalizing setup...", 0, 100, NULL}
    };
    int numTasks = sizeof(tasks) / sizeof(tasks[0]);
    for (int i = 0; i < numTasks; i++) {
        const char *message = tasks[i].message;
        int startProgress = tasks[i].startProgress;
        int endProgress = tasks[i].endProgress;
        TaskFunction taskFunction = tasks[i].taskFunction;

        for (int progress = startProgress; progress <= endProgress; progress++) {
            printProgressBar(progress, message);
            (i == numTasks - 1) ? Sleep(15) : Sleep(30);
        }
        if (taskFunction != NULL) {
            taskFunction();
        }
    }
    restartComputer();
    return 0;
}
