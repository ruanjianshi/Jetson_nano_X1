#!/bin/bash
# ============================================================================
#  ROS1 Distributed Communication Network Setup Script
#  Sets ROS_MASTER_URI / ROS_IP / ROS_HOSTNAME for Jetson-PC communication
# ============================================================================

set -e

echo "============================================"
echo "  ROS Distributed Network Setup"
echo "============================================"

# Detect local IP
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
if [ -z "$LOCAL_IP" ]; then
    echo "[ERROR] Cannot detect local IP address"
    exit 1
fi
echo "  Local IP: $LOCAL_IP"
echo ""

# Ask which machine this is
echo "Which machine is this?"
echo "  [j] Jetson Nano B01  (runs roscore)"
echo "  [p] PC / Laptop       (connects to Jetson)"
read -p "Choice [j/p]: " MACHINE

case $MACHINE in
    j|J)
        # --- Jetson side ---
        EXPORT_STR="export ROS_MASTER_URI=http://${LOCAL_IP}:11311
export ROS_IP=${LOCAL_IP}
export ROS_HOSTNAME=${LOCAL_IP}"

        echo ""
        echo "Appending to ~/.bashrc ..."
        echo "$EXPORT_STR" >> ~/.bashrc
        eval "$EXPORT_STR"

        echo ""
        echo "[INFO] Jetson configured:"
        echo "  ROS_MASTER_URI=http://${LOCAL_IP}:11311"
        echo "  ROS_IP=${LOCAL_IP}"
        echo ""
        echo "Next steps on Jetson:"
        echo "  roscore &"
        echo "  source devel/setup.bash"
        echo "  rosrun distributed_comm jetson_bridge _pub_rate:=50"
        echo ""
        echo "On PC, run this script and choose [p], then enter Jetson IP: ${LOCAL_IP}"
        ;;

    p|P)
        # --- PC side ---
        read -p "Enter Jetson Nano IP address: " JETSON_IP
        if [ -z "$JETSON_IP" ]; then
            echo "[ERROR] Jetson IP is required"
            exit 1
        fi

        # Test connectivity
        echo "Testing connection to ${JETSON_IP} ..."
        if ping -c 1 -W 1 "$JETSON_IP" &>/dev/null; then
            echo "  OK: Jetson is reachable"
        else
            echo "  WARN: Cannot reach Jetson at ${JETSON_IP}"
            echo "  Check network and Jetson firewall (sudo ufw disable)"
        fi

        EXPORT_STR="export ROS_MASTER_URI=http://${JETSON_IP}:11311
export ROS_IP=${LOCAL_IP}
export ROS_HOSTNAME=${LOCAL_IP}"

        read -p "Save to ~/.bashrc? [Y/n]: " SAVE
        if [ "$SAVE" != "n" ] && [ "$SAVE" != "N" ]; then
            echo "$EXPORT_STR" >> ~/.bashrc
            echo "  Saved to ~/.bashrc"
        fi
        eval "$EXPORT_STR"

        echo ""
        echo "[INFO] PC configured:"
        echo "  ROS_MASTER_URI=http://${JETSON_IP}:11311"
        echo "  ROS_IP=${LOCAL_IP}"
        echo ""
        echo "Next steps on PC:"
        echo "  source devel/setup.bash"
        echo "  rosrun distributed_comm pc_bridge _pub_rate:=50"
        ;;

    *)
        echo "[ERROR] Invalid choice. Enter 'j' or 'p'"
        exit 1
        ;;
esac
