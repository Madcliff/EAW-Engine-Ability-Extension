#!/bin/sh
# Builds the unified engine research PDF: dist/EAW-Engine-Research.pdf (needs pandoc and chromium).
# Regenerates docs/research/ENGINE_INDEX.md from the source first.
#   release/make_pdf.sh [version]
set -e
cd "$(dirname "$0")/.."
python3 -I tools/gen_engine_index.py
if [ -n "$1" ]; then python3 -I tools/build_research_pdf.py --version "$1"; else python3 -I tools/build_research_pdf.py; fi
