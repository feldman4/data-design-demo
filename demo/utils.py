import importlib
import inspect

import fire

import importlib
import inspect

def print_api():
    scrape_module_functions('demo.database')
    scrape_module_functions('demo.analysis')


def scrape_module_functions(module_name):
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        # print(f"Module {module_name} not found.")
        return

    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj):
            scrape_module_functions(f"{module_name}.{name}")
        elif inspect.isfunction(obj):
            print(f"Function path: {module_name}.{name}")
            print(f"Signature: {inspect.signature(obj)}")
            print(f"Docstring: {inspect.getdoc(obj)}\n")


def get_local_functions():
    current_module = inspect.currentframe().f_back.f_globals
    local_functions = []

    for name, obj in current_module.items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            local_functions.append(name)

    return local_functions


def main():
    local_functions = get_local_functions()
    cli = fire.Fire({func: globals()[func] for func in local_functions})

if __name__ == "__main__":
    main()
