#!/usr/bin/env bash
echo "Hello this is first attempt to run bash script on github actions"
OS=$(cat /etc/*release | grep ^NAME | tr -d 'NAME="')
ID=$(cat /etc/*release | grep ^ID | tr -d 'ID="')
VERSION_ID=$(cat /etc/*release | grep ^VERSION_ID | tr -d 'VERSION_ID="')

echo $OS
echo $ID
echo $VERSION_ID

if [ $VERSION_ID = "8" ]
then
    echo "This is centos8";
    export LC_ALL=C.UTF-8;
    export LANG=C.UTF-8;
    yum install -y python3 which git wget;
    yum install -y python3-pip python3-devel gcc;
    yum install -y python3-pytest beaker-client krb5-workstation krb5-devel;
elif [ $VERSION_ID = "7" ]
then
    echo "This is centos7";
    export LC_ALL="en_US";
    export LANG="en_US";
    yum install -y python3 which git wget;
    yum install -y python-pip python3-pip python3-devel gcc beaker-client krb5-workstation krb5-devel;
fi
