# SPIRIT PyRABBIT

This repository is part of the implementation for the SPIRIT project.

## Description
It contains code for the RABBIT transcoder in Python.

## Setup
Setup is easy using just.
```
    sudo apt install just
```

Further, install 7zip and some other tools:
```
    sudo apt update && sudo apt install -y p7zip-full wget
```

For some experiments, we patched NVIDIA Drivers to circumvent the 8 encoding session limit. Follow the (instrctions)[https://github.com/keylase/nvidia-patch.git]

### Encoding Data
First, we need to prepare data for the media server.
To encode the 8iVFBv2 dataset in quality R5 with a specified segment size to be hosted on the server, first, get the dataset:
```
    just download-8i
```
And then, build and run a transcoder-container which contains the mpeg-tmc2 test model for encoding:
```
    just build-transcoder
    just run-transcoder
```
In the container, run
```
    just encode-8i
```
to extend each sequence to 600 frames (looped) and encode them at R5 with segment lengths 1s, 2s and 4s.
If everything worked correctly, you should have a folder "/media/encoded/Xs_encodings" containing the .bin files.


## Experiments

### Latency/Transcoding Experiments
These experiments aim at testing configurations of experiments of the codec. An experiment can be done in the following way

Start a transcoder container (no service, just the tooling):
```
    just build-pyrabbit
    just run-pyrabbit
```

In the container, 
```
    cd /
    python3 scripts/transcoding_setting_experiment.py /configs/experiments/transcoding_times/settings.yaml
```


### Streaming Experiments
To prepare a streaming experiment (server-side), we will need to write a server configuration that describes the transcoding server behaviour.
Examples can be found in TODO.



## Usage
To run the container, start it interactively with
```
    just run-transcoder
```
## NVIDIA Drivers
```
# JUST (Makes life easier)
git clone https://mpr.makedeb.org/just
cd just
makedeb -si 

sudo apt update

# NVIDIA DRIVERS
sudo apt install --no-install-recommends -y build-essential
sudo apt install --no-install-recommends -y nvidia-driver-570

# DOCKER
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

After installation, you need to reboot (NVIDIA driver requires a reboot)

## Shared Filesystem
We will setup a shared file system (NFS) for the Media Server and the GPU Servers for /media and /media_cache
### On the server
``` 
sudo apt update
sudo apt install -y nfs-kernel-server

sudo mkdir -p /srv/media
sudo mkdir -p /srv/media_cache

sudo chown -R nobody:nogroup /srv/media /srv/media_cache
sudo chmod -R 777 /srv/media /srv/media_cache # Careful, not safe
```

and then add the following to /etc/exports:
```
/srv/media        *(ro,sync,no_subtree_check,no_root_squash)
/srv/media_cache  *(rw,sync,no_subtree_check,no_root_squash)
```
apply:
```
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

Verify with 
```
sudo exportfs -v
```
finally, mount:
```
sudo apt install -y nfs-common
sudo mkdir -p /media
sudo mkdir -p /media_cache
sudo mount 127.0.0.1:/srv/media /media
sudo mount 127.0.0.1:/srv/media_cache /media_cache
```
then add the following to /etc/fstab:
```
127.0.0.1:/srv/media       /media        nfs defaults,_netdev 0 0
127.0.0.1:/srv/media_cache /media_cache  nfs defaults,_netdev 0 0
```

### On the Workers:
```
sudo apt install -y nfs-common
sudo mkdir -p /media
sudo mkdir -p /media_cache
sudo mount 192.168.XX.XX:/srv/media /media
sudo mount 192.168.XX.XX:/srv/media_cache /media_cache
```

then add the following to /etc/fstab:
```
192.168.XX.XX:/srv/media       /media        nfs defaults,_netdev 0 0
192.168.XX.XX:/srv/media_cache /media_cache  nfs defaults,_netdev 0 0
```


# Setup
```
sudo apt install snapd
sudo snap install --edge --classic just

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

sudo snap set system homedirs=/userssudo snap set system homedirs=/users
```