#!/usr/bin/env bash
# install docker and config docker hub mirror from daocloud
# https://get.daocloud.io
docker run hello-world > /dev/null
if [ $? -ne 0 ]; then
    curl -sSL https://get.daocloud.io/docker | sh
    curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s http://c7a94599.m.daocloud.io
    echo "add current user to docker group"
    sudo groupadd docker
    sudo usermod -aG docker $USER
    echo "Docker Setup complete"
fi
echo -e "Creating Docker Image\n"
docker build -t 'crazybox' .
echo -e "\nRetrieving Installed Docker Images"
docker images
