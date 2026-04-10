#include "common_utils/logger.h"
#include <iostream>
#include <ctime>

namespace common_utils {

Logger::Logger(const std::string& node_name) : node_name_(node_name) {
    time_t now = time(nullptr);
    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y%m%d", localtime(&now));
    
    std::string filename = "logs/daily/" + std::string(buffer) + "_" + node_name + ".log";
    log_file_.open(filename, std::ios::app);
}

Logger::~Logger() {
    if (log_file_.is_open()) {
        log_file_.close();
    }
}

void Logger::info(const std::string& message) {
    log("INFO", message);
}

void Logger::warning(const std::string& message) {
    log("WARNING", message);
}

void Logger::error(const std::string& message) {
    log("ERROR", message);
}

void Logger::log(const std::string& level, const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    time_t now = time(nullptr);
    char buffer[80];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", localtime(&now));
    
    std::string log_entry = "[" + std::string(buffer) + "] [" + level + "] [" + node_name_ + "] " + message + "\n";
    
    if (log_file_.is_open()) {
        log_file_ << log_entry;
        log_file_.flush();
    }
    
    std::cout << log_entry;
}

} // namespace common_utils