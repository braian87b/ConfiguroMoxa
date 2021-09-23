#/bin/bash
# https://packaging.python.org/distributing/#working-in-development-mode

#only works after running build-package.sh
ls -lath ./src/dist/
pip3 install --no-cache-dir ./src/dist/ConfiguroMoxa-1.0-py3-none-any.whl
