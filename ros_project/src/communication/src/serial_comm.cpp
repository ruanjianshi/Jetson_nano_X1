#include "communication/serial_comm.h"
#include <iostream>

namespace communication {

SerialComm::SerialComm(const std::string& port, unsigned int baud_rate)
    : port_(port), baud_rate_(baud_rate), serial_(io_), connected_(false) {}

SerialComm::~SerialComm() {
    disconnect();
}

bool SerialComm::connect() {
    try {
        serial_.open(port_);
        serial_.set_option(boost::asio::serial_port_base::baud_rate(baud_rate_));
        serial_.set_option(boost::asio::serial_port_base::character_size(8));
        serial_.set_option(boost::asio::serial_port_base::parity(boost::asio::serial_port_base::parity::none));
        serial_.set_option(boost::asio::serial_port_base::stop_bits(boost::asio::serial_port_base::stop_bits::one));
        serial_.set_option(boost::asio::serial_port_base::flow_control(boost::asio::serial_port_base::flow_control::none));
        
        connected_ = true;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Serial connection error: " << e.what() << std::endl;
        return false;
    }
}

void SerialComm::disconnect() {
    if (connected_) {
        try {
            serial_.close();
        } catch (const std::exception& e) {
            std::cerr << "Serial disconnect error: " << e.what() << std::endl;
        }
        connected_ = false;
    }
}

bool SerialComm::write(const std::string& data) {
    if (!connected_) {
        return false;
    }
    
    try {
        boost::asio::write(serial_, boost::asio::buffer(data));
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Serial write error: " << e.what() << std::endl;
        return false;
    }
}

bool SerialComm::read(std::string& data) {
    if (!connected_) {
        return false;
    }
    
    try {
        char c;
        data.clear();
        
        while (boost::asio::read(serial_, boost::asio::buffer(&c, 1))) {
            data += c;
            if (data.size() > 1024) break; // Prevent buffer overflow
        }
        
        return !data.empty();
    } catch (const std::exception& e) {
        return false;
    }
}

} // namespace communication