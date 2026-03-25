#!/usr/bin/env bash

# fzf --version: 0.70.0 (eacef5ea)
# ripgrep 13.0.0
# Awk 5.1.0

# Search for string in every file of directory, showing context around the match.
# Usage: fzgrep.sh [dir] [ctx-preview-window-size]

set -euo pipefail
dir="${1:-.}"
ctx="${2:-10}"
cd "$dir"

awk_cmd="awk -v n={2} -v c=${ctx}"
awk_inside='NR>=n-c && NR<=n+c { if (NR==n) printf ">>> %5d %s\n", NR, $0; else printf " %5d %s\n", NR, $0 }'

fzf --ansi --disabled \
    --bind "start:reload:rg --line-number --no-heading --color=always ''" \
    --bind "change:reload:rg --line-number --no-heading --color=always {q} || true" \
    --delimiter : \
    --preview "${awk_cmd} '${awk_inside}' {1}"\
    --preview-window=up:60%
