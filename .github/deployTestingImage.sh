base_container=${1}

sed "s/BaseContainerImage/${base_container}/" ./dockerfile/Dockerfile -i

#yum install podman -y
name_prefix=$(echo ${base_container} | sed -e "s/://g")
podman login quay.io --username ${ secrets.QUAY_USERNAME } --password ${ secrets.QUAY_PASSWORD  }
podman build ./dockerfile/ -t ${name_prefix}-testing-teflo
podman tag ${name_prefix}-testing-teflo quay.io/junqizhang0/${name_prefix}-testing-teflo
podman push quay.io/junqizhang0/${name_prefix}-testing-teflo
sed "s/${name_prefix}/BaseContainerImage/" ./dockerfile/Dockerfile -i

