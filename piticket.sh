#!/bin/bash

# Update package list and install prerequisites
echo "Updating package lists..."
sudo apt-get update

echo "Installing prerequisites..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add permission to Pi User to Run Docker Commands
sudo usermod -aG docker pi

# Install Docker Compose
echo "Installing Docker Compose..."
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
sudo pip3 install docker-compose

# Create Docker Compose file for osTicket
echo "Creating Docker Compose file for osTicket..."
cat <<EOL >docker-compose.yml
version: '3'

services:
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: osticket
      MYSQL_USER: osticket
      MYSQL_PASSWORD: osticket
      MYSQL_DATABASE: osticket
  osticket:
    image: campbellsoftwaresolutions/osticket
    ports:
      - "8080:80"
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: osticket
      MYSQL_PASSWORD: osticket
      MYSQL_DATABASE: osticket
      OSTICKET_API_KEY: osticket
    depends_on:
      - mysql
EOL

# Deploy osTicket
echo "Deploying osTicket..."
docker-compose up -d

echo "osTicket should now be running on http://localhost:8080"
