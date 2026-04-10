#include "common_utils/config_loader.h"
#include <iostream>
#include <fstream>
#include <sstream>

namespace common_utils {

ConfigLoader::ConfigLoader() {
}

ConfigLoader::~ConfigLoader() {
}

bool ConfigLoader::loadConfig(const std::string& filepath, YAML::Node& config) {
    try {
        config = YAML::LoadFile(filepath);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error loading config: " << e.what() << std::endl;
        return false;
    }
}

} // namespace common_utils