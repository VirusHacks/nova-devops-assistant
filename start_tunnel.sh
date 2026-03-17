#!/bin/bash

# InfraGuard ngrok Tunnel Startup Script for macOS
# This script starts an ngrok tunnel on port 8000.
# If NGROK_DOMAIN is set in .env, it uses that for a permanent URL.

# Colors for output
CYAN='\033[0;36m'
GRAY='\033[0;90m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}--- Starting Nova-Devops-Automate ngrok Tunnel ---${NC}"

# 1. Kill any existing ngrok processes
echo -e "${GRAY}Cleaning up existing ngrok sessions...${NC}"
pkill ngrok 2>/dev/null

# 2. Load .env variables correctly
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 3. Apply Auth Token if present
if [ ! -z "$NGROK_AUTHTOKEN" ]; then
    ngrok config add-authtoken "$NGROK_AUTHTOKEN" > /dev/null
    echo -e "${GRAY}Applied ngrok authtoken.${NC}"
fi

# 4. Determine arguments
NGROK_ARGS="http 8000"
if [ ! -z "$NGROK_DOMAIN" ]; then
    DOMAIN=$(echo "$NGROK_DOMAIN" | sed -e 's|^https\?://||' -e 's|/.*$||')
    NGROK_ARGS="$NGROK_ARGS --url=$DOMAIN"
    echo -e "${YELLOW}Using static domain: $DOMAIN${NC}"
fi

# 5. Start ngrok in the background and log output
LOG_FILE="/tmp/ngrok.log"
echo "" > "$LOG_FILE"
ngrok $NGROK_ARGS > "$LOG_FILE" 2>&1 &
NGROK_PID=$!

# Ensure ngrok process stays alive for a moment
sleep 1
if ! kill -0 $NGROK_PID 2>/dev/null; then
    echo -e "${RED}Error: ngrok process failed to start immediately.${NC}"
    cat "$LOG_FILE"
    exit 1
fi

echo -e "${YELLOW}Waiting for ngrok to initialize...${NC}"
sleep 5

# 6. Fetch the public URL from ngrok's local API
RESPONSE=$(curl -s http://localhost:4040/api/tunnels)

if [ -z "$RESPONSE" ] || [ "$RESPONSE" == "{}" ]; then
    echo -e "${RED}Error: Failed to connect to ngrok local API or no tunnels found.${NC}"
    echo -e "${GRAY}ngrok log output:${NC}"
    cat "$LOG_FILE"
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

PUBLIC_URL=$(echo "$RESPONSE" | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4)

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${RED}Error: Public URL not found in API response.${NC}"
    echo -e "${GRAY}Full API Response: $RESPONSE${NC}"
    kill $NGROK_PID 2>/dev/null
    exit 1
else
    CLEAN_URL=$(echo "$PUBLIC_URL" | sed 's|/$||')
    echo -e "\n${GREEN}================================================${NC}"
    echo -e " PUBLIC WEBHOOK URL: \033[40;33m$CLEAN_URL/webhook/github\033[0m"
    echo -e "${GREEN}================================================${NC}\n"
    
    echo "1. Go to your GitHub App settings (Nova-Devops-Automate)."
    echo "2. Ensure 'Webhook URL' is set to the yellow URL above."
    echo "3. Ensure your local server is running on port 8000."
    echo -e "\n${GRAY}KEEP THIS WINDOW OPEN to keep the tunnel alive.${NC}"
    echo -e "${GRAY}Press Ctrl+C to stop the tunnel...${NC}"
    
    # Wait for the user to terminate the script
    # Use a loop to keep the script running and handle traps correctly
    while kill -0 $NGROK_PID 2>/dev/null; do
        sleep 1
    done
fi

# Cleanup on exit
function cleanup() {
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null
    fi
    echo -e "\n${CYAN}Tunnel stopped.${NC}"
    exit
}

trap cleanup INT TERM EXIT
