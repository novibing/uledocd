#!/usr/bin/env bash

cd -- "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || return 1 2>/dev/null || exit 1
_uledocd_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$OSTYPE" == "darwin"* ]]; then
	_data_dir="${HOME}/Library/Application Support/uledocd"
else
	_data_dir="${HOME}/.local/share/uledocd"
fi

_venv_dir="${_data_dir}/venv"

echo "Data directory: ${_data_dir}"
echo "Virtual environment directory: ${_venv_dir}"

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
unset _venv_dir
pip install -r ${_uledocd_dir}/requirements.txt
python3 uledocd_gui.py