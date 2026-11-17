#!/usr/bin/env bash

if [[ "$OSTYPE" == "darwin"* ]]; then
	_data_dir="${HOME}/Library/Application Support/uledocd"
else
	_data_dir="${HOME}/.local/share/uledocd"
fi

_venv_dir="${_data_dir}/venv"

echo
echo "Data directory: ${_data_dir}"
echo "Virtual environment directory: ${_venv_dir}"
echo

if [[ ! -d "${_data_dir}" ]]; then
	mkdir "${_data_dir}" || {
		echo "Failed to create data directory: ${_data_dir}" >&2
		return 1 2>/dev/null || exit 1
	}
fi

if [[ ! -d "${_venv_dir}" ]]; then
	python3 -m venv "${_venv_dir}" || {
		echo "Failed to create virtual environment: ${_venv_dir}" >&2
		return 1 2>/dev/null || exit 1
	}
fi

if [[ ! -f "${_venv_dir}/bin/activate" ]]; then
	echo "Virtual environment not found: ${_venv_dir}" >&2
	return 1 2>/dev/null || exit 1
fi

source "${_venv_dir}/bin/activate"
pip install --upgrade pip
pip install --upgrade uledocd
uledocd