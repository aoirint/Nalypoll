#!/bin/bash
sudo docker-compose exec app python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > TwiAnalyPolls/dump.json
