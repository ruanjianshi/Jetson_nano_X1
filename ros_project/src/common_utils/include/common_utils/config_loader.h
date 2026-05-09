#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>
#include <yaml-cpp/yaml.h>

namespace common_utils {

class ConfigLoader {
public:
    ConfigLoader();
    ~ConfigLoader();
    
    bool loadConfig(const std::string& filepath, YAML::Node& config);
};

} // namespace common_utils

#endif // CONFIG_LOADER_H