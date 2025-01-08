#!/usr/bin/env python3

from sys import argv
import os
import fnmatch
import yaml
import shutil
import subprocess

from colorama import Fore, Style

HOME_DIR = os.environ["HOME"]
USERPROFILE_FILE = ".userprofile"
AUTO_GENERATED_PREFIX_LINE = "# automatically generated by dotfiles ({})\n"

def printColoredName(fore: Fore, name: str):
    return fore + name + Style.RESET_ALL

def dotName(name: str):
    return printColoredName(Fore.MAGENTA, name)

def pathName(name: str):
    return printColoredName(Fore.GREEN, name)

def dirName(name: str):
    return printColoredName(Fore.BLUE, name)

def fileName(name: str):
    return printColoredName(Fore.CYAN, name)

def envName(name: str):
    return printColoredName(Fore.CYAN, name)

def commandName(name: str):
    return printColoredName(Fore.YELLOW, name)

def find_yml(dir):
    # List to store directories containing the .yml file
    dirs_with_yml = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(dir):
        # Check if any .yml file is in the current directory
        if any(fnmatch.fnmatch(file, "dot.yml") for file in files):
            dirs_with_yml.append(root)

    return len(dirs_with_yml) != 0

def create_dest(dest: str, backup: bool):
    if os.path.exists(dest):
        if backup:
            print("config directory already exists:", dest)
            i = 1
            backup_dir = dest + ".back." + str(i)
            while os.path.exists(backup_dir):
                print("backup already exists:", backup_dir)
                i = i + 1
                backup_dir = dest + ".back." + str(i)
            print ("creating backup:", pathName(backup_dir))
            shutil.copytree(dest, backup_dir)
    else:
        print("creating directory:", pathName(dest))
        os.makedirs(dest)

def install(dir: str):
    print("installing:", dotName(dir))
    yml_path = os.path.join(dir, "dot.yml")
    with open(yml_path, "r") as f:
        content = f.read()
        yml = yaml.load(content, Loader=yaml.CLoader)
        config = yml["config"]
        # Execute pre shell commands first
        if "pre_shell_commands" in config:
            pre_shell_commands = config["pre_shell_commands"]
            for pre_shell_command in pre_shell_commands:
                print("executing pre_shell_command", commandName(pre_shell_command))
                subprocess.run(pre_shell_command, shell=True)
        # if dest is $HOME, only copy files to home directory
        if config["dest"] == "$HOME":
            dest = HOME_DIR
        else:
            dest = os.path.expandvars(config["dest"])

            backup = True
            if "backup" in config and config["backup"] == False:
                backup = False

            create_dest(dest, backup)
        # Copy files
        if "files" in config:
            files = config["files"]
            for file in files:
                print("copying file", fileName(file), "to", pathName(dest))
                shutil.copy(os.path.join(dir, file), dest)
        # Copy directories
        if "directories" in config:
            directories = config["directories"]
            for directory in directories:
                print("copying directory", dirName(directory + "/"), "to", pathName(dest))
                basename = os.path.basename(directory)
                destination_dir = os.path.join(dest, basename)
                shutil.copytree(os.path.join(dir, directory), destination_dir, dirs_exist_ok=True)
        # Copy extra files
        if "extra_files" in config:
            extra_files = config["extra_files"]
            for extra_file in extra_files:
                extra_file_name = extra_file["name"]
                extra_file_dest = os.path.expandvars(extra_file["dest"])
                print("copying extra file", fileName(extra_file_name), "to", pathName(extra_file_dest))
                shutil.copy(os.path.join(dir, extra_file_name), extra_file_dest)
        # Write env variables
        if "env_vars" in config:
            env_vars = config["env_vars"]
            env_var_file = os.path.join(os.path.expandvars("$HOME"), USERPROFILE_FILE)
            with open(env_var_file, "a") as f:
                f.write(AUTO_GENERATED_PREFIX_LINE.format(dir))
                for env_var_dict in env_vars:
                    name = env_var_dict["name"]
                    value = env_var_dict["value"]
                    print("writing env var", envName(name), "to", pathName(env_var_file))
                    f.write("export {}=\"{}\"\n".format(name, value))
                f.write("\n")
        # Execute commands
        if "shell_commands" in config:
            shell_commands = config["shell_commands"]
            for shell_command in shell_commands:
                print("executing shell command", commandName(shell_command))
                subprocess.run(shell_command, shell=True)

        # Copy optional .userprofile
        if USERPROFILE_FILE in os.listdir(dir):
            home_userprofile = os.path.join(HOME_DIR, USERPROFILE_FILE)
            print("copying", fileName(USERPROFILE_FILE), "to", pathName(home_userprofile))
            with open(os.path.join(dir, USERPROFILE_FILE), "r") as f_source:
                content = f_source.read()
                with open(os.path.join(HOME_DIR, USERPROFILE_FILE), "a") as f_dest:
                    f_dest.write(AUTO_GENERATED_PREFIX_LINE.format(dir) + content + "\n")
    print()

def main():
    if len(argv) < 2:
        print("installing all dotfiles")
        # install for all directories that contain dot.yml file
        for path in os.listdir("."):
            if (find_yml(path)):
                install(path)
    else:
        dots = argv[1:]
        for dot in dots:
            if (find_yml(dot)):
                install(dot)

try:
    main()
except Exception as e:
    print("Error:", e)
    print("Usage: install_dots.py [<directory1> <directory2> ...]")