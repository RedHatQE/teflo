base_container=${1}

sed "s/BaseContainerImage/${base_container}/" ./dockerfile/Dockerfile -i

QUAY_USERNAME=${2}
QUAY_PASSWORD=${3}
#yum install podman -y
name_prefix=$(echo ${base_container} | sed -e "s/://g")
podman login quay.io --username ${QUAY_USERNAME} --password ${QUAY_PASSWORD}
podman build ./dockerfile/ -t ${name_prefix}-testing-teflo
podman tag ${name_prefix}-testing-teflo quay.io/junqizhang0/${name_prefix}-testing-teflo
podman push quay.io/junqizhang0/${name_prefix}-testing-teflo
sed "s/${base_container}/BaseContainerImage/" ./dockerfile/Dockerfile -i

