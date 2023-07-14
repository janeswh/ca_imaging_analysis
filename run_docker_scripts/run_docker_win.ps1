# gets directory where all experiment folders reside, assuming the docker img folder is in the same directory
$exp_dir = Split-Path -Path $PSScriptRoot -Parent

# load docker image
docker pull janeswh/ca_imaging_analysis

# set-variable -name IPADDRESS -value ((Test-Connection -ComputerName $Env:ComputerName -Count 1).IPV4Address.IPAddressToString + ":0.0") 

# apparently variable needs to be set this way in windows 11
$Env:IPADDRESS = ((Test-Connection -ComputerName $Env:ComputerName -Count 1).IPV4Address.IPAddressToString + ":0.0")

# moves up one directory to where the exp folders are
# cd ..

# changed IPADDRESS variable
# docker run --rm -it -e DISPLAY=$Env:IPADDRESS -p:8501:8501 -v "$(pwd):/app_dir/local_drive" janeswh/ca_imaging_analysis
docker run --rm -it -e DISPLAY=$Env:IPADDRESS -p:8501:8501 -v "${exp_dir}:/app_dir/local_drive" janeswh/ca_imaging_analysis

Read-Host -Prompt "Press enter to exit"
