#!/bin/bash

uuid | sha256sum |cut -d ' ' -f 1

