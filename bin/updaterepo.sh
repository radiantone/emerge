#!/bin/bash
python setup.py install
git add Dockerfile
git add README.md
git add .gitignore
git add docs
git add bin
git add emerge
git commit -m "Updates"
git push origin main
