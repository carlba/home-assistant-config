#!/bin/bash
for d in community/* ; do
    ln -s "$d" .
done
