#include "communication/network_comm.h"
#include <iostream>
#include <thread>

namespace communication {

NetworkComm::NetworkComm(const std::string& ip, int port)
    : acceptor_(io_), ip_(ip), port_(port), running_(false) {}

NetworkComm::~NetworkComm() {
    stopServer();
}

bool NetworkComm::startServer() {
    try {
        boost::asio::ip::tcp::endpoint endpoint(
            boost::asio::ip::address::from_string(ip_), port_);
        
        acceptor_.open(endpoint.protocol());
        acceptor_.set_option(boost::asio::socket_base::reuse_address(true));
        acceptor_.bind(endpoint);
        acceptor_.listen();
        
        running_ = true;
        acceptConnection();
        
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Network server error: " << e.what() << std::endl;
        return false;
    }
}

void NetworkComm::stopServer() {
    running_ = false;
    try {
        acceptor_.close();
    } catch (const std::exception& e) {
        std::cerr << "Stop server error: " << e.what() << std::endl;
    }
}

bool NetworkComm::broadcast(const std::string& message) {
    return true;
}

void NetworkComm::acceptConnection() {
    if (!running_) return;
    
    acceptor_.async_accept(
        [this](boost::system::error_code ec, boost::asio::ip::tcp::socket socket) {
            if (!ec) {
                handleConnection(std::move(socket));
            }
            acceptConnection();
        });
}

void NetworkComm::handleConnection(boost::asio::ip::tcp::socket socket) {
    try {
        std::string message = "Connected to server\n";
        boost::asio::write(socket, boost::asio::buffer(message));
    } catch (const std::exception& e) {
        std::cerr << "Handle connection error: " << e.what() << std::endl;
    }
}

} // namespace communication