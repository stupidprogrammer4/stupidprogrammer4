#!/usr/bin/env bash
set -euo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(dirname "$script_directory")"
output_path="${1:-$repository_root/assets/contributions.svg}"
temporary_file="$(mktemp)"
trap 'rm -f "$temporary_file"' EXIT

curl --fail --location --retry 3 --retry-all-errors --connect-timeout 10 --max-time 30 \
  "https://ghchart.rshah.org/27ff73/stupidprogrammer4" \
  --output "$temporary_file"

if [[ -f "$output_path" ]] && cmp --silent "$temporary_file" "$output_path"; then
  echo "Contribution calendar is already current."
  exit 0
fi

mkdir -p "$(dirname "$output_path")"
mv "$temporary_file" "$output_path"
trap - EXIT
echo "Updated $output_path"
