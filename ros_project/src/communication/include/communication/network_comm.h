#ifndef NETWORK_COMM_H
#define NETWORK_COMM_H

#include <string>
#include <boost/asio.hpp>
#include <boost/bind.hpp>

namespace communication {

class NetworkComm {
public:
    NetworkComm(const std::string& ip, int port);
    ~NetworkComm();
    
    bool startServer();
    void stopServer();
    bool broadcast(const std::string& message);
    
private:
    boost::asio::io_context io_;
    boost::asio::ip::tcp::acceptor acceptor_;
    std::string ip_;
    int port_;
    bool running_;
    
    void acceptConnection();
    void handleConnection(boost::asio::ip::tcp::socket socket);
};

} // namespace communication

#endif // NETWORK_COMM_H