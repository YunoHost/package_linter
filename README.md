# YunoHost apps package linter

Static analyzer that checks for common issues in Yunohost apps

## Usage
Make sure your `python --version` is >=3.11.0

```bash
git clone https://github.com/YunoHost/package_linter
cd package_linter
git clone https://github.com/<organization>/<app>_ynh
python -m venv ./venv # create vritual environment to avoid dependencies' conflict
source venv/bin/activate
pip install -r requirements.txt
./package_linter.py <app>_ynh
deactivate # if you want to quit the virtual environment
```
