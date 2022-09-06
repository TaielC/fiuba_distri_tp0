#!/usr/bin/env bash

network_name=${NETWORK_NAME:-tp0_testing_net}
server_uri=${SERVER_URI:-server}
server_port=${SERVER_PORT:-12345}


while true; do
    read -p "Enter input to send to server: " input
    if [ -z "$input" ]; then
        echo "Exiting..."
        exit 0
    fi

    cmd="echo \"Sending: $input\" && echo $input | nc $server_uri $server_port "
    docker run -it --rm --name test-with-netcat --network=$network_name bash:latest bash -c "$cmd"    
done
