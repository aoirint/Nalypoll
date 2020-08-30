#!/bin/bash
sudo docker-compose exec app python3 manage.py loaddata dump.json
