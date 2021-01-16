# Docker commands
- sudo docker image rm ubuntu:focal
- sudo docker build -t ubuntu:focal docker
- sudo docker run -it --rm -v /home/noa/tun-tap:/tun-tap/ --cap-add=NET_ADMIN ubuntu:focal

# Start script
- outside docker container
	- sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
- inside docker container
	- mkdir -p /dev/net
	- mknod /dev/net/tun c 10 200

# Temporary
- local
	- sudo python3 server.py --iface bob --endpoint 172.17.0.2:10000
- docker
	- python3 server.py --iface doc --endpoint 172.17.0.1:10000
