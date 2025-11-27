#!/bin/bash

EC2_USER="ec2-user"
EC2_IP="3.239.5.93"
EC2_KEY="claves-jenkins-ubuntu.pem"
IMAGE="oneiran/SecureDev:latest"

ssh -o StrictHostKeyChecking=no -i $EC2_KEY $EC2_USER@$EC2_IP "
  sudo docker stop app || true &&
  sudo docker rm app || true &&
  sudo docker pull $IMAGE &&
  sudo docker run -d --name app -p 80:5000 $IMAGE
"
