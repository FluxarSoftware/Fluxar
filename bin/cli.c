#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <Windows.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

const char *name = "Fluxar";
const char *file_extension = "fsc";
const char *cmd_class = "fluxar";

void run_script(char *script_file) {
    PyObject *pName, *pModule, *pFunc;
    PyObject *pArgs, *pValue;

    Py_Initialize();
    pName = PyUnicode_DecodeFSDefault("basic");
    if (!pName) {
        fprintf(stderr, "Error: cannot decode module name\n");
        exit(1);
    }

    pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        pFunc = PyObject_GetAttrString(pModule, "run");

        if (pFunc && PyCallable_Check(pFunc)) {
            pArgs = PyTuple_New(2);
            PyTuple_SetItem(pArgs, 0, PyUnicode_DecodeFSDefault("<stdin>"));
            PyTuple_SetItem(pArgs, 1, PyUnicode_DecodeFSDefault(script_file));

            pValue = PyObject_CallObject(pFunc, pArgs);
            Py_DECREF(pArgs);

            if (pValue != NULL) {
                PyObject_Print(pValue, stdout, Py_PRINT_RAW);
                Py_DECREF(pValue);
            } else {
                PyErr_Print();
            }
        } else {
            if (PyErr_Occurred()) {
                PyErr_Print();
            }
            fprintf(stderr, "Error: cannot find function 'run'\n");
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
        fprintf(stderr, "Error: cannot load module 'basic'\n");
    }
    Py_Finalize();
}

void init() {
    printf("Initializing project...\n");
    // Add your initialization logic here
}

void build(const char *script_name) {
    printf("Building script: %s\n", script_name);
    // Add your build logic here
}

void help() {
    printf("Usage: %s <command> <arg>\n", cmd_class);
    printf("Commands:\n");
    printf("    setup: Automatically set up %s to fit your computer.\n", name);
    printf("    run: Runs .%s files.\n", file_extension);
    printf("    build: Build a %s executable.\n", name);
}
int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("%s. Use 'help' command to see all commands.\n", name);
        return 1;
    }
    const char *command = argv[1];
    if (strcmp(command, "help") == 0) {
        help();
    } else if (strcmp(command, "run") == 0) {
         if (argc < 3) {
             printf("Usage: %s run <script>\n", argv[0]);
             exit(1);
         }
         char *script_file = argv[2];
         run_script(script_file);
    } else if (strcmp(command, "setup") == 0) {
         char command[1000];
         char dir_path[MAX_PATH];

         if (!GetCurrentDirectoryA(sizeof(dir_path), dir_path)) {
             fprintf(stderr, "\nError getting current directory\n");
             exit(1);
         }
         sprintf(command, "%s\\cmd\\setx.exe", dir_path);
         if (system(command) != 0) {
             fprintf(stderr, "Error setting up Fluxar\n");
             exit(1);
         }
    } else if (strcmp(command, "init") == 0) {
        init();
    } else if (strcmp(command, "build") == 0) {
        if (argc < 3) {
            printf("Usage: %s build <script>\n", cmd_class);
        }
        build(argv[2]);
    } else {
        printf("Unknown command: %s\n", command);
        help();
    }

    return 0;
}
