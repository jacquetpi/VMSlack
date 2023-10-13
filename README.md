VMStack is a IaaS scheduler prototype showing how multiple oversubscription levels can be considered on the same cluster of server.\\
It is composed of two elements : a local scheduler, deployed on each server, and a global scheduler.

Each server must be equipped with QEMU/KVM and libvirt.

## Setup

```bash
apt-get update && apt-get install -y git python3 python3.venv
git clone https://github.com/jacquetpi/vmpinning
cd vmpinning/
cp dotenv .env
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Configuration is being made by the ```.env``` file

## Local scheduler

Instance on each server
Deployed by default on 8099 port. Can be changed through the ```.env``` file

```bash
python3 -m schedulerlocal -h
python3 -m schedulerlocal --load=debug/topology_EPYC-7662.json
python3 -m schedulerlocal --load=debug/topology_i7-1185G7.json
python3 -m schedulerlocal --debug=1
```

Offline setting
```bash
python3 -m schedulerlocal --load=results/monitoring.csv --topology=debug/topology_EPYC-7662-exp.json
```

Online setting
```bash
source venv/bin/activate
python3 -m schedulerlocal
```
The local scheduler will run and wait for requests\\
Requests are made in a REST fashion way either, directly by a user, or by the global scheduler

Live setting : Order the creation of a vm
```bash
curl 'http://127.0.0.1:8099/deploy?name=example&cpu=2&mem=2&oc=2&qcow2=/var/lib/libvirt/images/hello.qcow2'
```
QCOW2 image must be pre-existant

Live setting : Order the deletion of a vm
```bash
curl 'http://127.0.0.1:8099/remove?name=example'
```

Live setting : Get the potential impact of a deployment on the Memory per core ratio
```bash
curl 'http://127.0.0.1:8099/progress?cpu=2&mem=2&oc=2'
```

## Global scheduler

Single instance in charge of selecting an appropriate host. Deploy
Deployed by default on 8100 port. Can be changed through the ```.env``` file

Online setting
```bash
source venv/bin/activate
python3 -m schedulerglobal
```
The global scheduler will run and wait for requests\\
Requests are made in a REST fashion way either

Live setting : Display status of each host
```bash
curl 'http://127.0.0.1:8100/status'
```

Live setting : Order the creation of a vm
```bash
curl 'http://127.0.0.1:8100/deploy?name=example&cpu=2&mem=2&oc=2&qcow2=/var/lib/libvirt/images/hello.qcow2'
QCOW2 image must be pre-existant (typically on a distributed storage mount point)
```

Live setting : Order the deletion of a vm
```bash
curl 'http://127.0.0.1:8100/remove?name=example'
```
VM names are considered unique