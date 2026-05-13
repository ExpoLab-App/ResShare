1) Install conda
2) Start new conda venv on python version 3.8 : conda create --name reschat_venv python=3.8
3) Activate new venv conda activate reschat_venv
4) install gcc and g++ : sudo apt install gcc-11
sudo apt install g++-11
5) Install C++ dependencies : sudo apt install openssl libssl-dev
6) Install bazel globally (if not installed)
    a) Install amd64.deb release from : http://github.com/bazelbuild/bazelisk/releases
    b) sudo apt install ./bazelisk-amd64.deb
    c) export USE_BAZEL_VERSION=7.5.0 (Strictly use this version or else build will fail)
    c) bazel --version
7) Install python dependencies : pip install -r requirements.txt
8) Bazel Build
    a) Ubuntu 22: bazel build //...
9) Install ipfs
    a) Download ipfs-daemon : 
        i) wget https://dist.ipfs.tech/kubo/v0.29.0/kubo_v0.29.0_linux-amd64.tar.gz
        ii) tar -xvzf kubo_v0.29.0_linux-amd64.tar.gz
        iii) cd kubo
        iv) sudo bash install.sh
        v) Ensure installation worked : ipfs --version
        vi) ipfs init
        vii) Start ipfs daemon : ipfs daemon
    b) Download ipfs-cluster-service : https://dist.ipfs.tech/ipfs-cluster-service/v1.1.4/ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz
        i) wget https://dist.ipfs.tech/ipfs-cluster-service/v1.1.4/ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz
        ii) tar -xvzf ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz
        iii) sudo mv ipfs-cluster-service/ipfs-cluster-service /usr/local/bin/
        iv) Ensure installation worked : ipfs-cluster-service --version
        i) ipfs-cluster-service init
        ii) ipfs-cluster-service daemon
10) export GOOGLE_API_KEY="your-gemini-api-key-here"
11) Update ipfs.config to "http://127.0.0.1:9094/
http://127.0.0.1:8080/" 
12) Run : python app.py



Frontend Setup:
Node Version 22.19.0
1) cd frontend & npm install
2) npm run start
