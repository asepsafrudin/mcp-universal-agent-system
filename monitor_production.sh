#!/bin/bash

# Ensure log directory exists
mkdir -p "$HOME/MCP/logs"

LOG_FILE="$HOME/MCP/logs/production_monitor.log"
ALERT_THRESHOLD_ERROR=5
ALERT_THRESHOLD_COST=5.00

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Fetch metrics
    # Using python to parse JSON might be safer if jq is not guaranteed, but usually jq is common.
    # Assuming jq is available as per user request.
    METRICS=$(curl -s http://localhost:8000/metrics/summary)
    
    # Check if metrics call failed
    if [ -z "$METRICS" ]; then
         echo "[$TIMESTAMP] ❌ Failed to fetch metrics (Server down?)" >> "$LOG_FILE"
         sleep 300
         continue
    fi

    # Extract key values using jq or fallback to grep/python if needed. 
    # Sticking to user provided script but adding robust jq check
    ERROR_COUNT=$(echo "$METRICS" | jq -r '.today.tasks_failed // 0')
    COST_TODAY=$(echo "$METRICS" | jq -r '.today.cost_usd // 0')
    SUCCESS_RATE=$(echo "$METRICS" | jq -r 'if (.today.tasks_completed + .today.tasks_failed) > 0 then (.today.tasks_completed / (.today.tasks_completed + .today.tasks_failed) * 100) else 0 end')
    
    # Log
    echo "[$TIMESTAMP] Errors: $ERROR_COUNT | Cost: \$$COST_TODAY | Success: $SUCCESS_RATE%" >> "$LOG_FILE"
    
    # Alert if thresholds exceeded
    # Using python for float comparison to be safe in bash
    if (( $(echo "$ERROR_COUNT >= $ALERT_THRESHOLD_ERROR" | bc -l) )); then
        echo "🚨 ALERT: High error count ($ERROR_COUNT)" | tee -a "$LOG_FILE"
        # TODO: Send notification (email, Telegram, etc)
    fi
    
    if (( $(echo "$COST_TODAY >= $ALERT_THRESHOLD_COST" | bc -l) )); then
        echo "💸 ALERT: Daily cost exceeded (\$$COST_TODAY)" | tee -a "$LOG_FILE"
        # TODO: Send notification
    fi
    
    sleep 300  # Check every 5 minutes
done
