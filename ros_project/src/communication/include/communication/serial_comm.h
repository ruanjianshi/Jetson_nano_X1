#ifndef SERIAL_COMM_H
#define SERIAL_COMM_H

#include <string>
#include <boost/asio.hpp>

namespace communication {

class SerialComm {
public:
    SerialComm(const std::string& port, unsigned int baud_rate);
    ~SerialComm();
    
    bool connect();
    void disconnect();
    bool write(const std::string& data);
    bool read(std::string& data);
    
private:
    boost::asio::io_context io_;
    boost::asio::serial_port serial_;
    std::string port_;
    unsigned int baud_rate_;
    bool connected_;
};

} // namespace communication

#endif // SERIAL_COMM_H