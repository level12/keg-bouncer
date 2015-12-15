# Usage:
# source scripts/make-env-venv.sh [env name=repo folder name by default]

repo=$(git rev-parse --show-toplevel)

envname=$1
if [ -z "$envname" ]; then
  envname=$(basename $repo)
fi

echo ~~~ Building virtual environment called \"$envname\" for repo \"$repo\".
rmvirtualenv $envname

pyenv local 2.7.10
mkvirtualenv $envname
workon $envname
pip install "git+https://github.com/level12/wheelhouse#egg=Wheelhouse"
wheelhouse install -- -r $repo/requirements/dev-env.txt
pip install -e .
rehash

echo ~~~ Run \"deactivate\" to leave temporary environment.
