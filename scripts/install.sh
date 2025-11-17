#!/bin/bash
# TweekIT MCP Installer Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

print_header "TweekIT MCP Server Installer"

echo ""
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 required but not installed"
    exit 1
fi
print_success "Python $(python3 --version | cut -d' ' -f2) found"

if ! command_exists pip3; then
    print_error "pip3 required"
    exit 1
fi
print_success "pip3 found"

echo ""
print_header "Installing TweekIT MCP Server"

print_info "Installing Python dependencies..."
pip3 install -e . || {
    print_error "Failed to install"
    exit 1
}
print_success "TweekIT MCP Server installed"

echo ""
print_header "API Configuration"

read -p "Do you have TweekIT API credentials? (y/n): " has_creds

if [[ $has_creds == "y" ]]; then
    read -p "Enter API Key: " api_key
    read -p "Enter API Secret: " api_secret
    
    cat > .env << EOF
TWEEKIT_API_KEY=$api_key
TWEEKIT_API_SECRET=$api_secret
EOF
    print_success "API credentials saved"
fi

echo ""
print_header "Installation Complete!"
echo ""
print_success "Ready to use!"
echo ""
echo "Launch web converter: ./scripts/launch-converter.sh"
echo ""
