#include "gpio_control/gpio_manager.h"
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace gpio_control {

GPIOManager::GPIOManager() : initialized_(false) {}

GPIOManager::~GPIOManager() {
    cleanup();
}

bool GPIOManager::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);
    initialized_ = true;
    return true;
}

void GPIOManager::cleanup() {
    std::lock_guard<std::mutex> lock(mutex_);
    for (int pin : configured_pins_) {
        unexportPin(pin);
    }
    configured_pins_.clear();
    initialized_ = false;
}

bool GPIOManager::setupPin(int pin, bool direction) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        exportPin(pin);
        
        std::string direction_path = "/sys/class/gpio/gpio" + std::to_string(pin) + "/direction";
        std::ofstream direction_file(direction_path);
        
        if (!direction_file.is_open()) {
            return false;
        }
        
        direction_file << (direction ? "out" : "in");
        direction_file.close();
        
        configured_pins_.push_back(pin);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error setting up pin " << pin << ": " << e.what() << std::endl;
        return false;
    }
}

bool GPIOManager::writePin(int pin, bool state) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::string value_path = "/sys/class/gpio/gpio" + std::to_string(pin) + "/value";
    std::ofstream value_file(value_path);
    
    if (!value_file.is_open()) {
        return false;
    }
    
    value_file << (state ? "1" : "0");
    value_file.close();
    
    return true;
}

bool GPIOManager::readPin(int pin, bool& state) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::string value_path = "/sys/class/gpio/gpio" + std::to_string(pin) + "/value";
    std::ifstream value_file(value_path);
    
    if (!value_file.is_open()) {
        return false;
    }
    
    std::string value_str;
    std::getline(value_file, value_str);
    value_file.close();
    
    state = (value_str == "1");
    return true;
}

void GPIOManager::setPinMode(int pin, const std::string& mode) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::string mode_path = "/sys/class/gpio/gpio" + std::to_string(pin) + "/direction";
    std::ofstream mode_file(mode_path);
    
    if (mode_file.is_open()) {
        mode_file << mode;
        mode_file.close();
    }
}

void GPIOManager::exportPin(int pin) {
    std::ofstream export_file("/sys/class/gpio/export");
    if (export_file.is_open()) {
        export_file << pin;
        export_file.close();
    }
}

void GPIOManager::unexportPin(int pin) {
    std::ofstream unexport_file("/sys/class/gpio/unexport");
    if (unexport_file.is_open()) {
        unexport_file << pin;
        unexport_file.close();
    }
}

} // namespace gpio_control