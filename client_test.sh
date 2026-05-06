#!/bin/bash

# Configuration
API_URL="http://127.0.0.1:8000"
USER_ID="user_12345"

echo "1. Submitting Job..."
# Submit the job and capture the job_id
RESPONSE=$(curl -s -X 'POST' "$API_URL/job" \
  -H 'Content-Type: application/json' \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"fasta_content\": \">4EBP_DROME\nMSASPTARQAITQALPMITRKVVISDPIQMPEVYSSTPGGTLYSTTPGGTKLIYERAFMKNLRGSPLSQTPPSNVPSCLLRGTPRTPFRKCVPVPTELIKQTKSLKIEDQEQFQLDL\",
    \"ptm_type\": [\"Phosphorylation_ST\", \"Phosphorylation_Y\"]
  }")

JOB_ID=$(echo $RESPONSE | grep -oP '(?<="job_id":")[^"]*')
echo "Job ID: $JOB_ID"

echo "2. Polling for completion..."
STATUS="Pending"
while [[ "$STATUS" == "Pending" || "$STATUS" == "Running" ]]; do
    sleep 2
    POLL_RES=$(curl -s -X 'GET' "$API_URL/job/$JOB_ID/status")
    STATUS=$(echo $POLL_RES | grep -oP '(?<="status":")[^"]*')
    echo "Current Status: $STATUS"
done

if [ "$STATUS" == "Finished" ]; then
    echo "3. Fetching Result..."
    curl -s -X 'GET' "$API_URL/job/$JOB_ID/result" | python3 -m json.tool
else
    echo "Job failed or was cancelled."
    echo $POLL_RES
fi