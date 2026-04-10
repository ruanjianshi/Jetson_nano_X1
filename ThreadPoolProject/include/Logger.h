#pragma once

#include <iostream>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <mutex>

class Logger {
public:
    static Logger& getInstance() {
        static Logger instance;
        return instance;
    }

    void log(const std::string& level, const std::string& message) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
        ss << '.' << std::setfill('0') << std::setw(3) << ms.count();
        
        std::string logLine = "[" + ss.str() + "] [" + level + "] " + message;
        
        std::cout << logLine << std::endl;
        
        logFile_ << logLine << std::endl;
        logFile_.flush();
    }

    void info(const std::string& message) {
        log("INFO", message);
    }

    void debug(const std::string& message) {
        log("DEBUG", message);
    }

    void warn(const std::string& message) {
        log("WARN", message);
    }

    void error(const std::string& message) {
        log("ERROR", message);
    }

    void testStart(const std::string& testName) {
        info("========== Test Start: " + testName + " ==========");
    }

    void testEnd(const std::string& testName) {
        info("========== Test End: " + testName + " ==========");
    }

private:
    Logger() {
        logFile_.open("logs/development.log", std::ios::app);
        logFile_ << "\n\n===== New Session =====\n" << std::endl;
    }

    ~Logger() {
        logFile_.close();
    }

    std::ofstream logFile_;
    std::mutex mutex_;
};

#define LOG_INFO(msg) Logger::getInstance().info(msg)
#define LOG_DEBUG(msg) Logger::getInstance().debug(msg)
#define LOG_WARN(msg) Logger::getInstance().warn(msg)
#define LOG_ERROR(msg) Logger::getInstance().error(msg)
#define TEST_START(name) Logger::getInstance().testStart(name)
#define TEST_END(name) Logger::getInstance().testEnd(name)