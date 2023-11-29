#!/bin/bash

export DOTNET_ROOT=$HOME/dotnet
export PATH=$PATH:$HOME/dotnet
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=0

source ./ENV/bin/activate
python3 -u ./lambda_function.py