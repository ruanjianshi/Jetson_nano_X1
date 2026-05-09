#ifndef GPIO_MANAGER_H
#define GPIO_MANAGER_H

#include <vector>
#include <string>
#include <mutex>

namespace gpio_control {

class GPIOManager {
public:
    GPIOManager();
    ~GPIOManager();
    
    bool initialize();
    void cleanup();
    
    bool setupPin(int pin, bool direction);
    bool writePin(int pin, bool state);
    bool readPin(int pin, bool& state);
    
    void setPinMode(int pin, const std::string& mode);
    
private:
    std::vector<int> configured_pins_;
    std::mutex mutex_;
    bool initialized_;
    
    void exportPin(int pin);
    void unexportPin(int pin);
};

} // namespace gpio_control

#endif // GPIO_MANAGER_H