# Usage:
# source scripts/make-env-vex.sh [env name=repo folder name by default]

repo=$(git rev-parse --show-toplevel)

envname=$1
if [ -z "$envname" ]; then
  envname=$(basename $repo)
fi

echo ~~~ Building temporary vex environment called \"$envname\" for repo \"$repo\".
rmvirtualenv $envname
vex -m --python python2.7 $envname pip install "git+https://github.com/level12/wheelhouse#egg=Wheelhouse"
vex $envname wheelhouse install -- -r $repo/requirements/dev-env.txt
vex $envname pip install -e .

echo ~~~ Run \"exit\" to leave and destroy temporary environment.
vex -r $envname
