#!/usr/bin/env bash
# Run one OpenROAD Flow Scripts configuration and preserve textual reports.
set -euo pipefail

if [[ $# -ne 1 ]] || [[ "$1" != "fixed" && "$1" != "generic-register-screen" && "$1" != "generic-sram-macro" ]]; then
    echo "usage: $0 {fixed|generic-register-screen|generic-sram-macro}" >&2
    exit 2
fi

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/../.." && pwd)
design=$1
image=${OPENROAD_IMAGE:-openroad/orfs}
report_dir="$repo_root/reports/inference_core/openroad/$design"
mkdir -p "$report_dir"

docker run --rm \
    -v "$repo_root:/work" \
    "$image" \
    bash -lc "set -o pipefail; cd /OpenROAD-flow-scripts; source ./env.sh; cd flow; make DESIGN_CONFIG=/work/inference_core/openroad/$design/config.mk 2>&1 | tee /work/reports/inference_core/openroad/$design/run.log; rc=\${PIPESTATUS[0]}; if [ -d results/sky130hd ]; then cp -R results/sky130hd /work/reports/inference_core/openroad/$design/results; fi; if [ -d reports/sky130hd ]; then cp -R reports/sky130hd /work/reports/inference_core/openroad/$design/reports; fi; exit \$rc"
