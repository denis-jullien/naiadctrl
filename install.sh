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
TRASH="🗑️"

set -e

# Trap to handle errors gracefully
trap 'error_exit "Installation failed at line $LINENO"' ERR

# Function to print fancy headers
print_header() {
    local text="$1"
    local width=60
    local text_length=${#text}
    local padding=$(((width - text_length - 2) / 2))
    local right_padding=$((width - text_length - padding - 3))

    echo
    echo -e "${PURPLE}╔$(printf '═%.0s' $(seq 1 $((width-2))))╗${NC}"
    printf "${PURPLE}║${WHITE}%*s%s%*s${PURPLE}║${NC}\n" $padding "" "$text" $right_padding ""
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

# Usage information
show_usage() {
    echo -e "${WHITE}Usage: $0 [OPTION]${NC}"
    echo -e "${CYAN}Options:${NC}"
    echo -e "  ${GREEN}install${NC}     Install $APP_NAME (default)"
    echo -e "  ${RED}uninstall${NC}   Remove $APP_NAME completely"
    echo -e "  ${BLUE}--help${NC}      Show this help message"
    echo
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

# Setup I2C and W1 sensor permissions and configuration
setup_sensor_permissions() {
    print_step "Setting Up I2C and W1 Sensor Permissions"

    local reboot_needed=false

    # Enable I2C interface if not already enabled
    if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
        print_info "Enabling I2C interface in /boot/config.txt"
        echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt > /dev/null
        reboot_needed=true
    else
        print_success "I2C interface already enabled"
    fi

    # Enable W1 (1-Wire) interface for temperature sensors
    if ! grep -q "^dtoverlay=w1-gpio" /boot/config.txt 2>/dev/null; then
        print_info "Enabling W1 (1-Wire) temperature sensors on GPIO17"
        echo "dtoverlay=w1-gpio,gpiopin=17" | sudo tee -a /boot/config.txt > /dev/null
        reboot_needed=true
    else
        print_success "W1 (1-Wire) interface already enabled"
    fi

    # Load I2C modules
    if ! lsmod | grep -q i2c_dev; then
        print_info "Loading I2C kernel modules"
        sudo modprobe i2c-dev 2>/dev/null || true
        if ! grep -q "i2c-dev" /etc/modules; then
            echo "i2c-dev" | sudo tee -a /etc/modules > /dev/null
        fi
    fi

    # Load W1 modules
    local w1_modules=("wire" "w1-gpio" "w1-therm")
    for module in "${w1_modules[@]}"; do
        if ! lsmod | grep -q "$module"; then
            print_info "Loading W1 kernel module: $module"
            sudo modprobe "$module" 2>/dev/null || true
            if ! grep -q "$module" /etc/modules; then
                echo "$module" | sudo tee -a /etc/modules > /dev/null
            fi
        fi
    done

    # Create i2c group if it doesn't exist
    if ! getent group i2c > /dev/null 2>&1; then
        sudo groupadd i2c
        print_success "Created i2c group"
    else
        print_success "i2c group already exists"
    fi

    # Add service user to required groups for sensor access
    local groups_to_add=("i2c" "gpio" "spi")
    for group in "${groups_to_add[@]}"; do
        if getent group "$group" > /dev/null 2>&1; then
            sudo usermod -a -G "$group" "$SERVICE_USER" 2>/dev/null || true
            print_success "Added $SERVICE_USER to $group group"
        else
            print_warning "$group group not found, skipping"
        fi
    done

    # Set up udev rules for I2C and W1 device permissions
    print_info "Setting up sensor device permissions"
    sudo tee /etc/udev/rules.d/99-sensors.rules > /dev/null << EOF
# I2C device permissions for $APP_NAME
SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0664"
KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0664"

# W1 (1-Wire) device permissions for temperature sensors
SUBSYSTEM=="w1_slave_driver", GROUP="gpio", MODE="0664"
KERNEL=="w1_bus_master*", GROUP="gpio", MODE="0664"
SUBSYSTEM=="w1", GROUP="gpio", MODE="0664"
EOF

    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger

    print_success "Sensor permissions configured"

    if [ "$reboot_needed" = true ]; then
        print_warning "Hardware interfaces enabled - reboot required after installation"
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
    echo -e "${BLUE}${PACKAGE} Installing: Python3, pip, venv, git, I2C tools...${NC}"

    {
        sudo apt install -y python3 python3-pip python3-venv git bc i2c-tools python3-smbus -qq
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

    # Setup sensor permissions (I2C and W1)
    setup_sensor_permissions

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
        sudo cp -r $APP_NAME-temp/backend/* $INSTALL_DIR/
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
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Additional security and resource limits
NoNewPrivileges=true
ProtectHome=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true

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

# Uninstall function
uninstall_app() {
    print_header "🗑️ UNINSTALLING $APP_NAME"

    print_step "Stopping and Disabling Service"
    if sudo systemctl is-active --quiet $APP_NAME; then
        sudo systemctl stop $APP_NAME
        print_success "Service stopped"
    fi

    if sudo systemctl is-enabled --quiet $APP_NAME 2>/dev/null; then
        sudo systemctl disable $APP_NAME -q
        print_success "Service disabled"
    fi

    print_step "Removing Service Files"
    if [ -f "/etc/systemd/system/$APP_NAME.service" ]; then
        sudo rm /etc/systemd/system/$APP_NAME.service
        print_success "Service file removed"
    fi

    sudo systemctl daemon-reload
    print_success "Systemd configuration reloaded"

    print_step "Removing Application Files"
    if [ -d "$INSTALL_DIR" ]; then
        sudo rm -rf $INSTALL_DIR
        print_success "Application directory removed"
    fi

    print_step "Removing Service User"
    if id "$SERVICE_USER" &>/dev/null; then
        sudo userdel $SERVICE_USER 2>/dev/null || true
        print_success "Service user removed"
    fi

    print_step "Cleaning Up Sensor Configuration"
    if [ -f "/etc/udev/rules.d/99-sensors.rules" ]; then
        sudo rm /etc/udev/rules.d/99-sensors.rules
        sudo udevadm control --reload-rules
        print_success "Sensor udev rules removed"
    fi

    # Ask if user wants to remove I2C group (only if no other users in it)
    if getent group i2c > /dev/null 2>&1; then
        local i2c_users=$(getent group i2c | cut -d: -f4)
        if [ -z "$i2c_users" ]; then
            read -p "Remove i2c group? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo groupdel i2c 2>/dev/null || true
                print_success "i2c group removed"
            fi
        else
            print_info "i2c group kept (other users still members)"
        fi
    fi

    print_header "✅ UNINSTALLATION COMPLETE"
    echo -e "${GREEN}${CHECK} $APP_NAME has been completely removed from your system${NC}"
    echo -e "${YELLOW}${CLOCK} Uninstallation completed at: $(date)${NC}"

    print_warning "Note: I2C and W1 interfaces remain enabled in /boot/config.txt"
    print_info "If you want to disable sensors completely, edit /boot/config.txt manually"
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
    echo -e "${CYAN}${WRENCH} Test I2C devices:${NC} sudo i2cdetect -y 1"
    echo -e "${CYAN}${WRENCH} List W1 sensors:${NC}  ls /sys/bus/w1/devices/"
    echo -e "${CYAN}${WRENCH} Read W1 sensor:${NC}   cat /sys/bus/w1/devices/28-*/w1_slave"
    echo -e "${CYAN}${WRENCH} Uninstall:${NC}       $0 uninstall"

    echo
    echo -e "${FIRE} ${GREEN}Your application is now running!${NC} ${FIRE}"
    echo -e "${YELLOW}${CLOCK} Installation completed at: $(date)${NC}"

    # Try to detect the service port and show access info
    if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
        echo -e "${BLUE}🌐 Access your application at: ${WHITE}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    fi

    # Check if I2C and W1 devices are available
    if command -v i2cdetect &> /dev/null; then
        echo -e "\n${BLUE}${GEAR} Sensor Status:${NC}"
        if [ -c /dev/i2c-1 ]; then
            print_success "I2C bus available at /dev/i2c-1"
        else
            print_warning "I2C device not found - may require reboot"
        fi

        if [ -d /sys/bus/w1/devices ]; then
            local w1_count=$(ls /sys/bus/w1/devices/ 2>/dev/null | grep -c "^28-" || echo "0")
            if [ "$w1_count" -gt 0 ]; then
                print_success "W1 temperature sensors detected: $w1_count"
            else
                print_info "No W1 temperature sensors detected (may require reboot or sensor connection)"
            fi
        else
            print_warning "W1 bus not available - may require reboot"
        fi
    fi
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-install}" in
        "install"|"")
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
            ;;
        "uninstall")
            clear
            print_banner
            check_root

            echo -e "\n${RED}${TRASH} About to uninstall $APP_NAME${NC}"
            echo -e "${YELLOW}⚠️  This will completely remove the application and all its data${NC}"
            read -p "Are you sure you want to continue? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                uninstall_app
            else
                echo -e "${BLUE}${CHECK} Uninstallation cancelled${NC}"
            fi
            ;;
        "--help"|"-h"|"help")
            print_banner
            show_usage
            ;;
        *)
            echo -e "${RED}${CROSS} Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"