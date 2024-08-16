# Afft - AUV File Formatting Tool

![ci](https://github.com/markvilar/raft/actions/workflows/ci.yml/badge.svg)
![pylint](https://github.com/markvilar/raft/actions/workflows/pylint.yml/badge.svg)

Raft is a collection of tools for working with data from ACFRs AUVs. The
tools consist of creating file queries from metadata, transferring files and 
directories, and parsing various data files. The repository includes support 
for the following tools:

The repository includes support for the following tools:
* poetry - package management and build system
* pytest - unit tests


## Getting started

### Install poetry

```shell
# Install pipenv
pip3 install --user poetry
```

### Configure the project environment

```shell
# Set the Python version 3.12
poetry env use 3.12

# Validate the environment configuration
poetry env info
```

### Install dependencies and build the project

```shell
# Install dependencies
poetry install

# Build the project
poetry build
```

### Running unit tests

```shell
poetry run pytest
```

### Running notebooks

```shell
poetry run jupyter notebook
```


## Other uses

### Managing the project environment

```shell
poetry env info
```

```shell
poetry env remove
```

### Activate the project environment in a shell

```shell
poetry shell
```

### Removing dependencies

```shell
poetry remove <package>
```
