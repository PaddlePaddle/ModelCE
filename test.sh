set -ex

function main {
    for cmd in git mongod redis-server python3; do
        check_command_exists $cmd
    done

    run_test
}

function run_test {
    export PYTHONPATH="$PWD"
    cd ce
    python3 test.py
}

function check_command_exists {
    cmd=$1
    if [ ! "$(command -v $cmd)" ]; then
        echo "command [${cmd}] not exists!"
        exit -1
    fi
}

main
