#!/bin/sh

export DOTNET_ROOT=$HOME/dotnet
export PATH=$PATH:$HOME/dotnet

python3 -u ./lambda_function.py