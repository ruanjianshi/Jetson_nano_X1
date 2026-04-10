#ifndef MCP2515_DRIVER_H
#define MCP2515_DRIVER_H

#include <cstdint>
#include <string>
#include <vector>
#include <mutex>
#include <thread>
#include <functional>

class MCP2515Driver
{
public:
    static constexpr uint8_t MCP2515_INT_PIN = 5;

    MCP2515Driver(int spi_bus = 0, int spi_device = 0, uint32_t bitrate = 500000, int sampling_point = 75);
    ~MCP2515Driver();

    bool connect();
    void disconnect();
    bool isConnected() const { return connected_; }

    bool initialize();
    bool reset();

    bool sendCanFrame(uint32_t can_id, const uint8_t* data, uint8_t dlc,
                      bool extended = false, bool remote = false);
    bool receiveCanFrame(uint32_t& can_id, uint8_t* data, uint8_t& dlc,
                         bool& extended, bool& remote);

    bool loopbackTest(uint32_t can_id = 0x123, const uint8_t* data = nullptr, uint8_t dlc = 4);

    void setReceiveCallback(std::function<void(uint32_t, const uint8_t*, uint8_t, bool, bool)> callback);
    void startRxThread();
    void stopRxThread();

private:
    int spi_bus_;
    int spi_device_;
    uint32_t bitrate_;
    int sampling_point_;
    int spi_fd_;
    bool connected_;
    std::mutex lock_;

    int int_pin_;
    bool gpio_initialized_;
    std::thread* rx_thread_;
    bool rx_thread_running_;
    std::function<void(uint32_t, const uint8_t*, uint8_t, bool, bool)> rx_callback_;

    static constexpr uint8_t SPI_INST_RESET = 0xC0;
    static constexpr uint8_t SPI_INST_READ = 0x03;
    static constexpr uint8_t SPI_INST_WRITE = 0x02;
    static constexpr uint8_t SPI_INST_RTS_0 = 0x81;
    static constexpr uint8_t SPI_INST_READ_STATUS = 0xA0;
    static constexpr uint8_t SPI_INST_RX_STATUS = 0xB0;
    static constexpr uint8_t SPI_INST_BIT_MODIFY = 0x05;

    static constexpr uint8_t REG_CANSTAT = 0x0E;
    static constexpr uint8_t REG_CANCTRL = 0x0F;
    static constexpr uint8_t REG_CNF3 = 0x28;
    static constexpr uint8_t REG_CNF2 = 0x29;
    static constexpr uint8_t REG_CNF1 = 0x2A;
    static constexpr uint8_t REG_CANINTE = 0x2B;
    static constexpr uint8_t REG_CANINTF = 0x2C;
    static constexpr uint8_t REG_EFLG = 0x2D;
    static constexpr uint8_t REG_TXB0CTRL = 0x30;
    static constexpr uint8_t REG_TXB0SIDH = 0x31;
    static constexpr uint8_t REG_TXB0SIDL = 0x32;
    static constexpr uint8_t REG_TXB0EID8 = 0x33;
    static constexpr uint8_t REG_TXB0EID0 = 0x34;
    static constexpr uint8_t REG_TXB0DLC = 0x35;
    static constexpr uint8_t REG_TXB0D0 = 0x36;
    static constexpr uint8_t REG_RXB0CTRL = 0x60;
    static constexpr uint8_t REG_RXB0SIDH = 0x61;
    static constexpr uint8_t REG_RXB0SIDL = 0x62;
    static constexpr uint8_t REG_RXB0EID8 = 0x63;
    static constexpr uint8_t REG_RXB0EID0 = 0x64;
    static constexpr uint8_t REG_RXB0DLC = 0x65;
    static constexpr uint8_t REG_RXB0D0 = 0x66;
    static constexpr uint8_t REG_RXB1CTRL = 0x70;
    static constexpr uint8_t REG_RXB1SIDH = 0x71;
    static constexpr uint8_t REG_RXB1SIDL = 0x72;
    static constexpr uint8_t REG_RXB1EID8 = 0x73;
    static constexpr uint8_t REG_RXB1EID0 = 0x74;
    static constexpr uint8_t REG_RXB1DLC = 0x75;
    static constexpr uint8_t REG_RXB1D0 = 0x76;

    static constexpr size_t BAUD_RATE_CONFIG_COUNT = 10;
    struct BaudRateConfig {
        uint32_t baud;
        uint8_t cnf1, cnf2, cnf3;
    };
    static const BaudRateConfig BAUD_RATE_CONFIGS[BAUD_RATE_CONFIG_COUNT];

    int spiTransfer(uint8_t* data, int len);
    uint8_t readRegister(uint8_t addr);
    void writeRegister(uint8_t addr, uint8_t value);
    void bitModify(uint8_t addr, uint8_t mask, uint8_t value);
    bool setMode(uint8_t mode);

    void rxLoop();
    bool waitForInterrupt(uint32_t timeout_ms);
};

#endif // MCP2515_DRIVER_H