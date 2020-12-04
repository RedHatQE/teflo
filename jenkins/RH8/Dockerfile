FROM registry.stage.redhat.io/openjdk/openjdk-11-rhel8
USER root
#Teflo requirements install python 3 as default python and python 2
RUN yum install -y python2-pip python2 python3-pip python3 gcc python2-devel python3-devel openssl-devel bzip2-devel libffi-devel make git \
&& alternatives --set python /usr/bin/python3 \
&& pip3 install virtualenv

# Teflo req install python 3.7
RUN cd /usr/src \
&& curl -s -k -O https://www.python.org/ftp/python/3.7.6/Python-3.7.6.tgz \
&& tar xzf Python-3.7.6.tgz \
&& cd Python-3.7.6 \
&& ./configure --enable-optimizations \
&& make altinstall \
&& rm /usr/src/Python-3.7.6.tgz
RUN echo $(python3.7 -V)

# Teflo req install python 3.8
RUN cd /usr/src \
&& curl -s -k -O https://www.python.org/ftp/python/3.8.1/Python-3.8.1.tgz \
&& tar xzf Python-3.8.1.tgz \
&& cd Python-3.8.1 \
&& ./configure --enable-optimizations \
&& make altinstall \
&& rm /usr/src/Python-3.8.1.tgz
RUN echo $(python3.8 -V)

#Teflo beaker requirements
RUN yum install -y krb5-workstation krb5-devel
RUN pip3 install beaker-client

ADD jenkins/slave-base/centralci/modify.sh /modify.sh

RUN sh /modify.sh

ADD jenkins/slave-base/contrib/* /usr/local/bin/

ADD jenkins/slave-base/contrib/bin/run-jnlp-client /usr/local/bin/run-jnlp-client

RUN chmod a+x /usr/local/bin/run-jnlp-client

ENTRYPOINT ["/usr/local/bin/run-jnlp-client"]

