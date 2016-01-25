# YunoHost apps package checker

Checker for YunoHost applications packages

## Use

```sh
git clone https://github.com/YunoHost/package_checker
cd package_checker
git clone https://github.com/<account>/<app>_ynh
./package_checker.py <app>_ynh
```

## Checks

* Check missing files
* Check manifest
 * syntax
 * missing fields
 * (field value)
* Check scripts
 * check bash header is present
 * check no sources are retrieve from internet via wget or curl for security reason
 * warn missing sudo before commands
 * make sure verifications are done before modifications on the system
