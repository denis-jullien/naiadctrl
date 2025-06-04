#!/bin/bash

# Configuration
APP_NAME="NaiadCtrl"
GITHUB_REPO="denis-jullien/naiadctrl"
INSTALL_DIR="/opt/$APP_NAME"
SERVICE_USER="$APP_NAME"
PYTHON_VERSION="3.9"

# Colors and styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# Unicode symbols
CHECK="✅"
CROSS="❌"
ARROW="➤"
STAR="⭐"
GEAR="⚙️"
ROCKET="🚀"
PACKAGE="📦"
WRENCH="🔧"
CLOCK="⏰"
FIRE="🔥"

set -e

# Trap to handle errors gracefully
trap 'error_exit "Installation failed at line $LINENO"' ERR

# Function to print fancy headers
print_header() {
    local text="$1"
    local width=60
    echo
    echo -e "${PURPLE}╔$(printf '═%.0s' $(seq 1 $((width-2))))╗${NC}"
    printf "${PURPLE}║${WHITE}%*s${PURPLE}║${NC}\n" $(((${#text}+$width-2)/2)) "$text"
    echo -e "${PURPLE}╚$(printf '═%.0s' $(seq 1 $((width-2))))╝${NC}"
    echo
}

# Function to print step headers
print_step() {
    echo -e "\n${CYAN}${BOLD}${ARROW} $1${NC}"
    echo -e "${DIM}$(printf '─%.0s' $(seq 1 50))${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

# Function to print error messages
error_exit() {
    echo -e "\n${RED}${CROSS} ERROR: $1${NC}" >&2
    echo -e "${YELLOW}${CLOCK} Installation interrupted. Check the logs above for details.${NC}" >&2
    exit 1
}

# Function to print info messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Animated spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Progress bar
progress_bar() {
    local duration=$1
    local steps=50
    echo -ne "${CYAN}"
    for ((i=0; i<=steps; i++)); do
        printf "\r${GEAR} Progress: ["
        printf "%*s" $i | tr ' ' '█'
        printf "%*s" $((steps-i)) | tr ' ' '░'
        printf "] %d%%" $((i*100/steps))
        sleep $(echo "scale=3; $duration/$steps" | bc -l 2>/dev/null || echo "0.05")
    done
    echo -e "${NC}"
}

# ASCII Art Banner
print_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║    ███╗   ██╗ █████╗ ██╗ █████╗ ██████╗  ██████╗████████╗██████╗ ██╗         ║
    ║    ████╗  ██║██╔══██╗██║██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██║         ║
    ║    ██╔██╗ ██║███████║██║███████║██║  ██║██║        ██║   ██████╔╝██║         ║
    ║    ██║╚██╗██║██╔══██║██║██╔══██║██║  ██║██║        ██║   ██╔══██╗██║         ║
    ║    ██║ ╚████║██║  ██║██║██║  ██║██████╔╝╚██████╗   ██║   ██║  ██║███████╗    ║
    ║    ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝    ║
    ║                                                                              ║
    ║                   AUTOMATED INSTALLER                                        ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# System info detection
detect_system() {
    print_step "Detecting System Information"

    OS=$(lsb_release -si 2>/dev/null || echo "Unknown")
    ARCH=$(uname -m)
    KERNEL=$(uname -r)

    echo -e "${BLUE}🖥️  Operating System: ${WHITE}$OS${NC}"
    echo -e "${BLUE}⚡ Architecture: ${WHITE}$ARCH${NC}"
    echo -e "${BLUE}🧠 Kernel: ${WHITE}$KERNEL${NC}"

    if [[ "$ARCH" != "armv7l" && "$ARCH" != "aarch64" ]]; then
        print_warning "This script is optimized for Raspberry Pi (ARM architecture)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    print_success "System detection complete"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error_exit "Please do not run this script as root. Use sudo when needed."
    fi
}

# Prerequisites check
check_prerequisites() {
    print_step "Checking Prerequisites"

    local missing_deps=()

    # Check for required commands
    for cmd in curl git sudo systemctl; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        else
            print_success "$cmd is available"
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        error_exit "Missing required commands: ${missing_deps[*]}"
    fi

    # Check internet connectivity
    echo -n "Testing internet connectivity... "
    if ping -c 1 github.com &> /dev/null; then
        print_success "Internet connection OK"
    else
        error_exit "No internet connection available"
    fi
}

# Main installation function
main_install() {
    print_header "🚀 STARTING INSTALLATION OF $APP_NAME"

    # Update system with progress
    print_step "Updating System Packages"
    print_info "This may take a few minutes..."

    {
        sudo apt update -qq
        sudo apt upgrade -y -qq
    } &
    spinner $!
    wait
    print_success "System packages updated"

    # Install dependencies
    print_step "Installing Dependencies"
    echo -e "${BLUE}${PACKAGE} Installing: Python3, pip, venv, git...${NC}"

    {
        sudo apt install -y python3 python3-pip python3-venv git bc -qq
    } &
    spinner $!
    wait
    print_success "Dependencies installed"

    # Create service user
    print_step "Setting Up Service User"
    if sudo useradd --system --home $INSTALL_DIR --shell /bin/false $SERVICE_USER 2>/dev/null; then
        print_success "Service user '$SERVICE_USER' created"
    else
        print_info "Service user '$SERVICE_USER' already exists"
    fi

    # Create installation directory
    print_step "Preparing Installation Directory"
    sudo mkdir -p $INSTALL_DIR
    sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    print_success "Installation directory prepared: $INSTALL_DIR"

    # Download application
    print_step "Downloading Application from GitHub"
    echo -e "${BLUE}${PACKAGE} Repository: https://github.com/$GITHUB_REPO${NC}"

    cd /tmp
    rm -rf $APP_NAME-temp
    {
        git clone --depth 1 https://github.com/$GITHUB_REPO.git $APP_NAME-temp -q
        sudo cp -r $APP_NAME-temp/* $INSTALL_DIR/
        sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
        rm -rf $APP_NAME-temp
    } &
    spinner $!
    wait
    print_success "Application downloaded successfully"

    # Setup Python environment
    print_step "Setting Up Python Virtual Environment"
    cd $INSTALL_DIR

    {
        sudo -u $SERVICE_USER python3 -m venv venv
        sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip -q
        if [ -f requirements.txt ]; then
            sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt -q
        fi
    } &
    spinner $!
    wait
    print_success "Python environment ready"

    # Create systemd service
    print_step "Creating System Service"

    sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=$APP_NAME Web Service 🚀
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created"

    # Enable and start service
    print_step "Starting Service"
    echo -e "${BLUE}${GEAR} Enabling and starting $APP_NAME service...${NC}"

    progress_bar 2

    sudo systemctl daemon-reload
    sudo systemctl enable $APP_NAME -q
    sudo systemctl start $APP_NAME

    sleep 2

    if sudo systemctl is-active --quiet $APP_NAME; then
        print_success "Service started successfully"
    else
        print_warning "Service may have issues. Check logs with: sudo journalctl -u $APP_NAME"
    fi
}

# Final status and instructions
show_completion() {
    print_header "🎉 INSTALLATION COMPLETE!"

    local status=$(sudo systemctl is-active $APP_NAME)
    local enabled=$(sudo systemctl is-enabled $APP_NAME)

    echo -e "${GREEN}${STAR} Application: ${WHITE}$APP_NAME${NC}"
    echo -e "${GREEN}${STAR} Status: ${WHITE}$status${NC}"
    echo -e "${GREEN}${STAR} Auto-start: ${WHITE}$enabled${NC}"
    echo -e "${GREEN}${STAR} Installation Path: ${WHITE}$INSTALL_DIR${NC}"

    echo
    print_header "📋 USEFUL COMMANDS"
    echo -e "${CYAN}${WRENCH} Check status:${NC}    sudo systemctl status $APP_NAME"
    echo -e "${CYAN}${WRENCH} View logs:${NC}       sudo journalctl -u $APP_NAME -f"
    echo -e "${CYAN}${WRENCH} Restart service:${NC} sudo systemctl restart $APP_NAME"
    echo -e "${CYAN}${WRENCH} Stop service:${NC}    sudo systemctl stop $APP_NAME"
    echo -e "${CYAN}${WRENCH} Disable service:${NC} sudo systemctl disable $APP_NAME"

    echo
    echo -e "${FIRE} ${GREEN}Your application is now running!${NC} ${FIRE}"
    echo -e "${YELLOW}${CLOCK} Installation completed at: $(date)${NC}"

    # Try to detect the service port and show access info
    if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
        echo -e "${BLUE}🌐 Access your application at: ${WHITE}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    fi
}

# Main execution
main() {
    clear
    print_banner

    check_root
    detect_system
    check_prerequisites

    echo -e "\n${YELLOW}${CLOCK} Ready to install $APP_NAME${NC}"
    echo -e "${DIM}Press Ctrl+C to cancel, or wait 5 seconds to continue...${NC}"

    for i in {5..1}; do
        echo -ne "\rStarting in $i seconds... "
        sleep 1
    done
    echo -e "\rStarting installation!     "

    main_install
    show_completion
}

# Run main function
main "$@"
