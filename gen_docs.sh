#!/usr/bin/env bash

cd src
pdoc --html -o ../docs --force .
cd ../
git add docs
