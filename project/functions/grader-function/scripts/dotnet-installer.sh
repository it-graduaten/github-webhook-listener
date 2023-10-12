ARCH=$(uname -m)

if [ "$ARCH" == "x86_64" ]; then
    echo "Running on x86_64 architecture"

    wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb 
    dpkg -i packages-microsoft-prod.deb
    apt update 
    apt install dotnet-sdk-6.0 -y

elif [ "$ARCH" == "aarch64" ]; then
    echo "Running on aarch64 architecture"

    wget https://download.visualstudio.microsoft.com/download/pr/df31fc1b-3db2-48c3-81f1-dade77100315/3cdb20ce781adcc51fd6058ebe32a8c9/dotnet-sdk-6.0.415-linux-arm64.tar.gz
    mkdir -p $HOME/dotnet && tar zxf dotnet-sdk-6.0.415-linux-arm64.tar.gz -C $HOME/dotnet
    export DOTNET_ROOT=$HOME/dotnet
    export PATH=$PATH:$HOME/dotnet

else
    echo "Unsupported architecture: $ARCH"
fi
