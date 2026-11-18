#!/usr/bin/env bash
set -e
python seed.py
exec streamlit run app.py --server.port "${PORT:-8600}" --server.address 0.0.0.0

