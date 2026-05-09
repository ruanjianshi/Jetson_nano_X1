#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <fstream>
#include <mutex>

namespace common_utils {

class Logger {
public:
    Logger(const std::string& node_name);
    ~Logger();
    
    void info(const std::string& message);
    void warning(const std::string& message);
    void error(const std::string& message);
    
private:
    std::string node_name_;
    std::ofstream log_file_;
    std::mutex mutex_;
    
    void log(const std::string& level, const std::string& message);
};

} // namespace common_utils

#endif // LOGGER_H