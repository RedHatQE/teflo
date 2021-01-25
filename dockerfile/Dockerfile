
FROM "BaseContainerImage"
#install all the dependencies and then use the non-root
run yum install -y gcc python3 python3-devel python3-pip krb5-workstation krb5-devel \
    && pip3 install virtualenv tox \
    && groupadd teflo \
    && adduser -g teflo teflo -s /bin/sh
run sh -c "sudo chmod -R 777 /github"
