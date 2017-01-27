# YunoHost apps package linter

Linter for YunoHost applications packages

## Usage

```bash
git clone https://github.com/YunoHost/package_linter
cd package_linter
git clone https://github.com/<account>/<app>_ynh
./package_linter.py <app>_ynh
```

## Checks

* Check missing files
* Check manifest
 * syntax
 * missing fields
 * missing type
 * (field value)
* Check scripts
 * warn missing sudo before commands
 * make sure verifications are done before modifications on the system
 * check non usage of helpers and propose them

## License

* GNU AGPLv3
