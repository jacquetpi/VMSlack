Intro

## Setup

```bash
apt-get update && apt-get install -y git python3 python3.venv
git clone https://github.com/jacquetpi/vmpinning
cd vmpinning/
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Local

```bash
python3 -m schedulerlocal -h
python3 -m schedulerlocal --load=debug/cpuset_EPYC-7662.json
python3 -m schedulerlocal --load=debug/cpuset_i7-1185G7.json
python3 -m schedulerlocal --debug=1
```