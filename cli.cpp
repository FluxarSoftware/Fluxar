#include <iostream>
#include <string>
#include <filesystem>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <vector>
#include <sstream>
#include <dlfcn.h>
#include <Python.h>

namespace fs = std::filesystem;

const std::string name = "Fluxar";
const std::string version = "1.0.0";
const std::string file_extension = "fsc";
const std::string cmd_class = "fluxar";

// Function to run a Python script
void run_script(const std::string& script_file) {
    Py_Initialize();
    PyObject* pName = PyUnicode_FromString("src.lang.handler");
    PyObject* pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject* pFunc = PyObject_GetAttrString(pModule, "cors_run");

        if (pFunc && PyCallable_Check(pFunc)) {
            PyObject* pArgs = PyTuple_Pack(1, PyUnicode_FromString(script_file.c_str()));
            PyObject* pResult = PyObject_CallObject(pFunc, pArgs);
            Py_DECREF(pArgs);

            if (pResult != NULL) {
                PyObject* repr = PyObject_Repr(pResult);
                std::cout << PyUnicode_AsUTF8(repr) << std::endl;
                Py_DECREF(repr);
                Py_DECREF(pResult);
            } else {
                PyErr_Print();
                std::cerr << "Failed to run script" << std::endl;
            }
        } else {
            if (PyErr_Occurred()) PyErr_Print();
            std::cerr << "Cannot find function 'cors_run'" << std::endl;
        }

        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
        std::cerr << "Failed to load module 'src.lang.handler'" << std::endl;
    }

    Py_Finalize();
}

// Function to setup the environment
void setup() {
    std::string system_os = std::string(getenv("OS") ? getenv("OS") : "");
    fs::path dir_path = fs::current_path();
    fs::path path = dir_path / "src" / "cmd" / (system_os == "Windows_NT" ? "setup.dll" : "setup.dynlib");
    try {
        if (system_os == "Windows_NT") {
            // Use LoadLibrary and GetProcAddress in Windows instead of ctypes
        } else {
            // Linux/macOS specific code
            void* handle = dlopen(path.c_str(), RTLD_LAZY);
            if (!handle) {
                throw std::runtime_error(dlerror());
            }
            typedef void (*start_func)();
            start_func start = (start_func)dlsym(handle, "start");
            if (start) {
                start();
            } else {
                throw std::runtime_error(dlerror());
            }
            dlclose(handle);
        }
    } catch (const std::exception& e) {
        std::cerr << "\nError setting up Fluxar: " << e.what() << std::endl;
    }
}

// Function to initialize a project
void init() {
    std::string template_dir = "./init_template";
    std::string project_name;
    std::cout << "Enter the project name: ";
    std::getline(std::cin, project_name);
    std::string project_dir = fs::current_path() / project_name;

    try {
        fs::copy(template_dir, project_dir, fs::copy_options::recursive);
        std::cout << "Initialized project '" << project_name << "' successfully." << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing project: " << e.what() << std::endl;
    }
}

// Function to build a project
void build(const std::string& script_name) {
    std::string command = "build.exe " + script_name;
    int result = std::system(command.c_str());
    if (result != 0) {
        std::cerr << "Error building script: " << script_name << std::endl;
    }
}

// Function to show available commands
void show_commands() {
    std::vector<std::string> commands = {
        "run <script>: Run a Fluxar script.",
        "setup: Setup the Fluxar environment.",
        "init: Initialize a new Fluxar project.",
        "build <script>: Build a Fluxar project.",
        "--version: Show the current version.",
        "--help: Show help information."
    };
    std::cout << "Available commands:" << std::endl;
    for (const auto& command : commands) {
        std::cout << "  " << command << std::endl;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << cmd_class << " <command> [arg]" << std::endl;
        return 1;
    }

    std::string command = argv[1];
    if (command == "--version") {
        std::cout << name << " version " << version << std::endl;
    } else if (command == "--help") {
        show_commands();
    } else if (command == "run") {
        if (argc < 3) {
            std::cerr << "Usage: " << cmd_class << " run <script>" << std::endl;
            return 1;
        }
        run_script(argv[2]);
    } else if (command == "setup") {
        setup();
    } else if (command == "init") {
        init();
    } else if (command == "build") {
        if (argc < 3) {
            std::cerr << "Usage: " << cmd_class << " build <script>" << std::endl;
            return 1;
        }
        build(argv[2]);
    } else if (command == "--list-commands") {
        show_commands();
    } else {
        std::cerr << "Unknown command: " << command << std::endl;
        return 1;
    }

    return 0;
}