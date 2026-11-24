#!/bin/sh
set -eu
if [ ! -f /home/node/.n8n/.ortelana-imported-v2 ]; then
  n8n import:workflow --input=/workflows/manual-analysis.json
  n8n import:workflow --input=/workflows/scheduled-analysis.json
  touch /home/node/.n8n/.ortelana-imported-v2
fi
# Bootstrap one existing, narrowly scoped automation identity. Approval tokens are never given to n8n.
node -e 'const fs=require("fs");fs.writeFileSync("/tmp/ortelana-credentials.json",JSON.stringify([{id:"ortelanaApiHeader",name:"Ortelana API automation",type:"httpHeaderAuth",data:{name:"Authorization",value:"Bearer "+process.env.ORTELANA_AUTOMATION_TOKEN}}]),{mode:0o600});'
n8n import:credentials --input=/tmp/ortelana-credentials.json
rm -f /tmp/ortelana-credentials.json
exec n8n start
