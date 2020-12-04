FROM docker-registry.engineering.redhat.com/centralci/jnlp-slave-base:1.5
#Teflo general requirements
RUN yum install -y gcc python-devel \
 && curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" \
 && python get-pip.py \ 
 && yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
 && yum install -y python36 python36-devel\
 && pip install virtualenv
#Teflo beaker requirements
RUN curl -o /etc/yum.repos.d/bkr-client.repo https://beaker-project.org/yum/beaker-client-CentOS.repo \
 && yum install -y beaker-client \ 
 && yum install -y krb5-workstation krb5-devel
#Teflo Linchpin libvirt requirements
RUN yum install -y libvirt-devel libguestfs-tools python-libguestfs
ENV LANG=en_US.utf8 LC_ALL=en_US.utf8
