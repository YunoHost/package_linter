#!/usr/bin/env python3

import sys
import os
import json

class c:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	END = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def header(app_path):
	print(c.UNDERLINE + c.HEADER + c.BOLD + "YUNOHOST APP PACKAGE CHECKER\n" + c.END)
	print("App packaging documentation: https://yunohost.org/#/packaging_apps")
	print("App package example: https://github.com/YunoHost/example_ynh\n")
	print("Checking " + c.BOLD + app_path + c.END + " package\n")

def print_right(str):
	print(c.OKGREEN + "✔", str, c.END)

def print_wrong(str):
	print(c.FAIL + "✘", str, c.END)

def check_files_exist(app_path):
	"""
	Check files exist
	"""
	print (c.BOLD + c.HEADER + ">>>> MISSING FILES <<<<" + c.END);
	fname = ("manifest.json", "scripts/install", "scripts/remove", \
	"scripts/upgrade", "scripts/backup", "scripts/restore", "LICENSE", "README.md")
	i = 0;
	while (i < len(fname)):
		if (check_file_exist(app_path + "/" + fname[i])): print_right(fname[i])
		else: print_wrong(fname[i])
		i+=1

def check_file_exist(file_path):
	return 1 if os.path.isfile(file_path) else 0

def read_file(file_path):
	with open(file_path) as f:
		file = f.read().splitlines()
	return file

def check_manifest(manifest):
	print (c.BOLD + c.HEADER + "\n>>>> MANIFEST <<<<" + c.END);
	"""
	Check if there is no comma syntax issue
	"""
	try:
		with open(manifest, encoding='utf-8') as data_file:
			manifest = json.loads(data_file.read())
		print_right("Manifest syntax is good.")
	except: print_wrong("There is a syntax (comma) issue in manifest.json. Can't do following tests."); return
	i, fields = 0, ("name", "id", "description", "url", "license", \
	"maintainer", "multi_instance", "services", "arguments")
	while (i < len(fields)): 
		if fields[i] in manifest: print_right("\"" + fields[i] + "\" fields is present")
		else: print_wrong("\"" + fields[i] + "\" field is missing")
		i+=1
	
# Check under array
#		manifest["description"]["en"]
#		manifest["maintainer"]["name"]
#		manifest["maintainer"]["email"]
#		manifest["arguments"]["install"]
	"""
	Check values in keys
	"""
	if "license" in manifest and manifest["license"] != "free" and manifest["license"] != "non-free":
		print_wrong("You should specify 'free' or 'non-free' software package in the license field.")
	elif "license" in manifest: print_right("'licence' key value is good.")
	if "multi_instance" in manifest and manifest["multi_instance"] != "true" and manifest["multi_instance"] != "false":
		print_wrong("multi_instance field must use 'true' or 'false' value.");
	if "services" in manifest:
		services = ("nginx", "php5-fpm", "mysql", "uwsgi", "metronome")
		i = 0
		while (i < len(manifest["services"])):
			if manifest["services"][i] not in services:
				print(manifest["services"][i] + " service doesn't exist")
			i+=1
	if "install" in manifest["arguments"]:
		types = ("domain", "path", "password")
		i = 0
		while (i < len(types)):
			j = 0
			while (j < len(manifest["arguments"]["install"])):
				if types[i] == manifest["arguments"]["install"][j]["name"]:
					if "type" not in manifest["arguments"]["install"][j]:
						print("You should specify " + types[i] + " type: \"type\": \"" + types[i] + "\",")
				j+=1
			i+=1
def check_install_script(install_path):
	if check_file_exist(install_path) == 0: return
	print (c.BOLD + c.HEADER + "\n>>>> INSTALL SCRIPT <<<<" + c.END);
	install = read_file(install_path)
	check_script_header_presence(install)
	check_sudo_prefix_commands(install)
	check_verifications_done_before_modifying_system(install)
	if "wget" in install or "curl" in install:
		print("You should not fetch sources from internet with curl or wget for security reasons.")

def check_remove_script(remove_path):
	if check_file_exist(remove_path) == 0: return
	print (c.BOLD + c.HEADER + "\n>>>> REMOVE SCRIPT <<<<" + c.END);
	remove = read_file(remove_path)
	check_script_header_presence(remove)
	check_sudo_prefix_commands(remove)
	check_verifications_done_before_modifying_system(remove)

def check_script_header_presence(script):
	if "#!/bin/bash" in script[0]: print_right("Script contain at first line \"#!/bin/bash\"")
	else: print_wrong("Script must contain at first line \"#!/bin/bash\"")

def check_sudo_prefix_commands(script):
	"""
	Check if commands are prefix with "sudo"
	"""
	cmd = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", \
	"service", "yunohost", "find" "swapon", "mkswap", "useradd")#, "dd")
	i, ok = 0, 1
	while i < len(script):
		j = 0
		while j < len(cmd):
			if cmd[j] + " " in script[i] and "sudo " + cmd[j] + " " not in script[i] \
			and "yunohost service" not in script[i] and "-exec " + cmd[j] not in script[i] \
			and ".service" not in script[i] and script[i][0] != '#':
				print(c.FAIL + "✘ Line ", i + 1, "you should add \"sudo\" before this command line:", c.END)
				print(script[i]); ok = 0
			j+=1
		i+=1
	if ok == 1: print_right("All commands are prefix with \"sudo\".")

def check_verifications_done_before_modifying_system(script):
	"""
	Check if verifications are done before modifying the system
	"""
	ex, i = 0, 0
	while i < len(script):
		if "exit" in script[i]: ex = i
		i+=1
	cmd = ("cp", "mkdir", "rm", "chown", "chmod", "apt-get", "apt", "service", \
	"find", "sed", "mysql", "swapon", "mount", "dd", "mkswap", "useradd")#"yunohost"
	i, ok = 0, 1
	while i < len(script):
		if i >= ex: break
		j = 0
		while (j < len(cmd)):
			if cmd[j] in script[i]:
				print(c.FAIL + "✘ At line", i + 1, "\"" + cmd[j] + "\" command is executed before verifications are made." + c.END)
				print("This system modification is an issue if a verification exit the script.")
				print("You should move this command bellow verifications."); ok = 0
			j+=1
		i+=1
	if ok == 1: print_right("Verifications (with exit commands) are done before any system modifications.")

if __name__ == '__main__':
	os.system("clear")
	if len(sys.argv) != 2: print("Give one app package path."); exit()
	app_path = sys.argv[1]
	header(app_path)
	check_files_exist(app_path)
	check_manifest(app_path + "/manifest.json")
	check_install_script(app_path + "/scripts/install")
	check_remove_script(app_path + "/scripts/remove")
	"""
	check_upgrade_script(app_path + "/scripts/upgrade")
	check_backup_script(app_path + "/scripts/backup")
	check_restore_script(app_path + "/scripts/restore")
	"""


"""
## Todo ##
* Si nginx dans les services du manifest, vérifier :
	* présence de /conf/nginx.conf
	* sudo service reload nginx dans les scripts install, remove, upgrade, restore (backup n’est pas nécessaire)

* Helper propositions
	if "apt" in install: print("You should use this helper: \"sudo yunohost \".")

* use jsonchema to check the manifest
https://github.com/YunoHost/yunotest/blob/master/apps_tests/manifest_schema.json
https://github.com/YunoHost/yunotest/blob/master/apps_tests/__init__.py
"""
