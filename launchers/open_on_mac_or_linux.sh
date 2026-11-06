#!/usr/bin/env bash
# Opens the study's notebook on macOS or Linux. Run:  bash launchers/open_on_mac_or_linux.sh
# The first run sets up a private copy of Python and the study's packages inside this folder.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [ ! -f src/shapdp.py ]; then
    echo "Please run this file from inside the study's folder."
    exit 1
fi

# Everything goes inside this folder. Deleting the folder removes all of it.
STUDY_ENV="$PWD/.study_environment"
UV_VERSION=0.13.6
PYTHON_VERSION=3.14.7
export UV_CACHE_DIR="$STUDY_ENV/cache"
export UV_PYTHON_INSTALL_DIR="$STUDY_ENV/python"
export UV_PYTHON_BIN_DIR="$STUDY_ENV/bin"
export UV_PYTHON_PREFERENCE=only-managed
export UV_NO_CONFIG=1
export JUPYTER_CONFIG_DIR="$STUDY_ENV/jupyter/config"
export JUPYTER_DATA_DIR="$STUDY_ENV/jupyter/data"
export JUPYTER_RUNTIME_DIR="$STUDY_ENV/jupyter/runtime"
export IPYTHONDIR="$STUDY_ENV/ipython"
export MPLCONFIGDIR="$STUDY_ENV/matplotlib"

failed() {
    echo
    echo "Something went wrong. Check the internet connection and run this file again."
    echo "If it still fails, delete the folder .study_environment here and try once more."
    echo "You can read all the results without installing anything: open"
    echo "notebook/reproduce_results.html in a browser."
}

# The private Python only works in the folder where it was set up, so moving this folder repeats the setup.
if [ "$(cat "$STUDY_ENV/ready.txt" 2> /dev/null)" != "$PWD" ]; then
    trap failed ERR
    rm -rf "$STUDY_ENV"
    case "$(uname -s)-$(uname -m)" in
        Darwin-arm64)              TARGET=aarch64-apple-darwin ;;
        Darwin-x86_64)             TARGET=x86_64-apple-darwin ;;
        Linux-x86_64)              TARGET=x86_64-unknown-linux-gnu ;;
        Linux-aarch64|Linux-arm64) TARGET=aarch64-unknown-linux-gnu ;;
        *) echo "This system is not supported: $(uname -s) $(uname -m)"; exit 1 ;;
    esac

    echo
    echo "First time only: setting up a private copy of Python and the study's packages."
    echo "It needs an internet connection and installs nothing outside this folder."
    echo
    mkdir -p "$STUDY_ENV"

    echo "[1 of 4] Downloading the installer..."
    curl -fsSL -o "$STUDY_ENV/uv.tar.gz" \
        "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-$TARGET.tar.gz"
    tar -xzf "$STUDY_ENV/uv.tar.gz" -C "$STUDY_ENV" --strip-components=1

    echo "[2 of 4] Getting Python $PYTHON_VERSION..."
    "$STUDY_ENV/uv" python install "$PYTHON_VERSION"

    echo "[3 of 4] Creating the environment..."
    "$STUDY_ENV/uv" venv --python "$PYTHON_VERSION" "$STUDY_ENV/venv"

    echo "[4 of 4] Installing the exact package versions..."
    "$STUDY_ENV/uv" pip sync --python "$STUDY_ENV/venv/bin/python" --require-hashes requirements-notebook.lock

    # Register the private kernel, so that Jupyter does not pick up another Python on this computer.
    "$STUDY_ENV/venv/bin/python" -m ipykernel install --user --name python3 --display-name "Python 3"

    echo "$PWD" > "$STUDY_ENV/ready.txt"
    trap - ERR
fi

PYTHON="$STUDY_ENV/venv/bin/python"
if [ "${1:-}" = "--check" ]; then
    "$PYTHON" -m nbconvert --to notebook --execute --inplace \
        --ExecutePreprocessor.timeout=1800 notebook/reproduce_results.ipynb
    "$PYTHON" -m nbconvert --to html notebook/reproduce_results.ipynb
    echo "CHECK PASSED"
    exit 0
fi

echo
echo "Opening the notebook in your browser."
echo "Keep this window open while you use it. Close it when you finish."
echo
"$PYTHON" -m notebook notebook/reproduce_results.ipynb
