# gets directory where all experiment folders reside, assuming the docker img folder is in the same directory
# $exp_dir = Split-Path -Path $PSScriptRoot -Parent

# load docker image
docker load -i roi_analysis_0.1.0.tar

# set-variable -name IPADDRESS -value ((Test-Connection -ComputerName $Env:ComputerName -Count 1).IPV4Address.IPAddressToString + ":0.0") 

# apparently variable needs to be set this way in windows 11
$Env:IPADDRESS = ((Test-Connection -ComputerName $Env:ComputerName -Count 1).IPV4Address.IPAddressToString + ":0.0")

# moves up one directory to where the exp folders are
cd ..

# docker run --rm -it -e DISPLAY=$IPADDRESS -p:8501:8501 -v "$(pwd):/app/local_drive" roi_analysis_0.1.0

# changed IPADDRESS variable
docker run --rm -it -e DISPLAY=$Env:IPADDRESS -p:8501:8501 -v "$(pwd):/app/local_drive" roi_analysis_0.1.0


Read-Host -Prompt "Press enter to exit"