#include "mcp2515_driver.h"
#include <iostream>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <cstring>
#include <thread>
#include <chrono>

const MCP2515Driver::BaudRateConfig MCP2515Driver::BAUD_RATE_CONFIGS[MCP2515Driver::BAUD_RATE_CONFIG_COUNT] = {
    {125000, 0x03, 0x90, 0x02},
    {250000, 0x01, 0x90, 0x02},
    {500000, 0x00, 0x90, 0x02},
    {800000, 0x00, 0x80, 0x01},
    {125000, 0x03, 0x98, 0x01},
    {250000, 0x01, 0x98, 0x01},
    {500000, 0x00, 0x98, 0x01},
    {125000, 0x03, 0xAC, 0x03},
    {250000, 0x01, 0xAC, 0x03},
    {500000, 0x00, 0xAC, 0x03}
};

MCP2515Driver::MCP2515Driver(int spi_bus, int spi_device, uint32_t bitrate, int sampling_point)
    : spi_bus_(spi_bus), spi_device_(spi_device), bitrate_(bitrate),
      sampling_point_(sampling_point),
      spi_fd_(-1), connected_(false), int_pin_(MCP2515_INT_PIN),
      gpio_initialized_(false), rx_thread_(nullptr), rx_thread_running_(false)
{
}

MCP2515Driver::~MCP2515Driver()
{
    stopRxThread();
    disconnect();
}

bool MCP2515Driver::connect()
{
    std::string spi_path = "/dev/spidev" + std::to_string(spi_bus_) + "." + std::to_string(spi_device_);
    spi_fd_ = ::open(spi_path.c_str(), O_RDWR);
    if (spi_fd_ < 0) {
        std::cerr << "ERROR: Failed to open SPI device: " << spi_path << std::endl;
        return false;
    }

    uint32_t speed = 1000000;
    if (ioctl(spi_fd_, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        std::cerr << "ERROR: Failed to set SPI speed" << std::endl;
        ::close(spi_fd_);
        spi_fd_ = -1;
        return false;
    }

    uint8_t mode = 0;
    if (ioctl(spi_fd_, SPI_IOC_WR_MODE, &mode) < 0) {
        std::cerr << "ERROR: Failed to set SPI mode" << std::endl;
        ::close(spi_fd_);
        spi_fd_ = -1;
        return false;
    }

    uint8_t bits = 8;
    if (ioctl(spi_fd_, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
        std::cerr << "ERROR: Failed to set SPI bits per word" << std::endl;
        ::close(spi_fd_);
        spi_fd_ = -1;
        return false;
    }

    connected_ = true;
    std::cout << "OK: SPI connection established: " << spi_path << " @ 1MHz" << std::endl;
    return true;
}

void MCP2515Driver::disconnect()
{
    if (spi_fd_ >= 0) {
        ::close(spi_fd_);
        spi_fd_ = -1;
    }
    connected_ = false;
}

int MCP2515Driver::spiTransfer(uint8_t* data, int len)
{
    if (!connected_ || spi_fd_ < 0) {
        return -1;
    }

    std::lock_guard<std::mutex> lock(lock_);

    struct spi_ioc_transfer tr;
    memset(&tr, 0, sizeof(tr));
    tr.tx_buf = reinterpret_cast<unsigned long>(data);
    tr.rx_buf = reinterpret_cast<unsigned long>(data);
    tr.len = len;
    tr.speed_hz = 1000000;
    tr.bits_per_word = 8;

    if (ioctl(spi_fd_, SPI_IOC_MESSAGE(1), &tr) < 0) {
        std::cerr << "ERROR: SPI transfer failed" << std::endl;
        return -1;
    }

    return len;
}

uint8_t MCP2515Driver::readRegister(uint8_t addr)
{
    uint8_t tx_data[3] = {SPI_INST_READ, addr, 0x00};
    if (spiTransfer(tx_data, 3) < 0) {
        return 0;
    }
    return tx_data[2];
}

void MCP2515Driver::writeRegister(uint8_t addr, uint8_t value)
{
    uint8_t tx_data[3] = {SPI_INST_WRITE, addr, value};
    spiTransfer(tx_data, 3);
}

void MCP2515Driver::bitModify(uint8_t addr, uint8_t mask, uint8_t value)
{
    uint8_t tx_data[4] = {SPI_INST_BIT_MODIFY, addr, mask, value};
    spiTransfer(tx_data, 4);
}

bool MCP2515Driver::setMode(uint8_t mode)
{
    writeRegister(REG_CANCTRL, mode);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    uint8_t stat = readRegister(REG_CANSTAT);
    if (stat != 0xFF) {
        uint8_t current_mode = (stat >> 5) & 0x07;
        return current_mode == (mode >> 5);
    }
    return false;
}

bool MCP2515Driver::reset()
{
    uint8_t cmd = SPI_INST_RESET;
    if (spiTransfer(&cmd, 1) < 0) {
        return false;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    return true;
}

bool MCP2515Driver::initialize()
{
    if (!connected_) {
        return false;
    }

    std::cout << "Initializing MCP2515 (8MHz crystal)..." << std::endl;
    reset();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    writeRegister(REG_CANCTRL, 0x80);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    if (readRegister(REG_CANCTRL) != 0x80) {
        std::cerr << "ERROR: Failed to enter configuration mode" << std::endl;
        return false;
    }

    BaudRateConfig cfg;
    bool found = false;

    if (sampling_point_ >= 80) {
        for (size_t i = 0; i < 4; ++i) {
            if (BAUD_RATE_CONFIGS[i].baud == bitrate_) {
                cfg = BAUD_RATE_CONFIGS[i];
                found = true;
                break;
            }
        }
    } else if (sampling_point_ >= 70) {
        for (size_t i = 4; i < 7; ++i) {
            if (BAUD_RATE_CONFIGS[i].baud == bitrate_) {
                cfg = BAUD_RATE_CONFIGS[i];
                found = true;
                break;
            }
        }
    } else {
        for (size_t i = 7; i < 10; ++i) {
            if (BAUD_RATE_CONFIGS[i].baud == bitrate_) {
                cfg = BAUD_RATE_CONFIGS[i];
                found = true;
                break;
            }
        }
    }

    if (!found) {
        std::cerr << "ERROR: Unsupported baudrate: " << bitrate_ << std::endl;
        return false;
    }

    writeRegister(REG_CNF1, cfg.cnf1);
    writeRegister(REG_CNF2, cfg.cnf2);
    writeRegister(REG_CNF3, cfg.cnf3);

    uint8_t v2 = readRegister(REG_CNF2);
    if (v2 != cfg.cnf2) {
        std::cerr << "ERROR: CNF2 write failed: expected 0x" << std::hex << (int)cfg.cnf2
                  << ", got 0x" << (int)v2 << std::dec << std::endl;
        return false;
    }
    std::cout << "OK: Baudrate " << bitrate_ << " bps configured" << std::endl;
    std::cout << "    CNF1=0x" << std::hex << (int)cfg.cnf1
              << " CNF2=0x" << (int)cfg.cnf2 << " CNF3=0x" << (int)cfg.cnf3 << std::dec << std::endl;

    writeRegister(REG_RXB0CTRL, 0x60);
    writeRegister(REG_RXB1CTRL, 0x60);

    writeRegister(REG_CANINTF, 0x00);
    writeRegister(REG_CANINTE, 0x03);
    writeRegister(REG_CANINTF, 0x80);

    writeRegister(REG_CANCTRL, 0x00);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    uint8_t stat = readRegister(REG_CANSTAT);
    uint8_t mode = (stat >> 5) & 0x07;
    std::cout << "OK: Initialization complete, CANSTAT=0x" << std::hex << (int)stat
              << ", mode=" << (int)mode << std::dec << std::endl;
    return true;
}

bool MCP2515Driver::sendCanFrame(uint32_t can_id, const uint8_t* data, uint8_t dlc,
                                  bool extended, bool remote)
{
    if (!connected_) {
        return false;
    }
    if (dlc > 8) {
        return false;
    }

    uint8_t intf = readRegister(REG_CANINTF);
    if (intf & 0x04) {
        bitModify(REG_CANINTF, 0x04, 0x00);
    }

    int timeout = 50;
    while (timeout > 0) {
        uint8_t ctrl = readRegister(REG_TXB0CTRL);
        if ((ctrl & 0x08) == 0) {
            break;
        }
        bitModify(REG_TXB0CTRL, 0x08, 0x00);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        timeout--;
    }
    if (timeout <= 0) {
        std::cerr << "ERROR: TXB0 busy" << std::endl;
        return false;
    }

    uint8_t sidh, sidl, eid8 = 0, eid0 = 0;
    if (extended) {
        if (can_id > 0x1FFFFFFF) {
            return false;
        }
        sidh = (can_id >> 21) & 0xFF;
        sidl = (((can_id >> 18) & 0x07) << 5) | 0x08 | ((can_id >> 16) & 0x03);
        eid8 = (can_id >> 8) & 0xFF;
        eid0 = can_id & 0xFF;
        writeRegister(REG_TXB0EID8, eid8);
        writeRegister(REG_TXB0EID0, eid0);
    } else {
        if (can_id > 0x7FF) {
            return false;
        }
        sidh = (can_id >> 3) & 0xFF;
        sidl = ((can_id & 0x07) << 5) & 0xE0;
        writeRegister(REG_TXB0EID8, 0);
        writeRegister(REG_TXB0EID0, 0);
    }

    writeRegister(REG_TXB0SIDH, sidh);
    writeRegister(REG_TXB0SIDL, sidl);

    uint8_t dlc_byte = dlc & 0x0F;
    if (remote) {
        dlc_byte |= 0x40;
    }
    writeRegister(REG_TXB0DLC, dlc_byte);

    for (uint8_t i = 0; i < dlc; ++i) {
        writeRegister(REG_TXB0D0 + i, data[i]);
    }
    for (uint8_t i = dlc; i < 8; ++i) {
        writeRegister(REG_TXB0D0 + i, 0);
    }

    uint8_t rts_cmd = SPI_INST_RTS_0;
    spiTransfer(&rts_cmd, 1);

    timeout = 200;
    while (timeout > 0) {
        intf = readRegister(REG_CANINTF);
        if (intf & 0x04) {
            bitModify(REG_CANINTF, 0x04, 0x00);
            return true;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        timeout--;
    }

    std::cerr << "ERROR: Send timeout" << std::endl;
    return false;
}

bool MCP2515Driver::receiveCanFrame(uint32_t& can_id, uint8_t* data, uint8_t& dlc,
                                      bool& extended, bool& remote)
{
    if (!connected_) {
        return false;
    }

    uint8_t intf = readRegister(REG_CANINTF);
    if (intf == 0xFF) {
        return false;
    }

    uint8_t buf = 0;
    uint8_t base = REG_RXB0SIDH;
    uint8_t dlc_addr = REG_RXB0DLC;
    uint8_t data_base = REG_RXB0D0;

    if (intf & 0x01) {
        buf = 0;
        base = REG_RXB0SIDH;
        dlc_addr = REG_RXB0DLC;
        data_base = REG_RXB0D0;
    } else if (intf & 0x02) {
        buf = 1;
        base = REG_RXB1SIDH;
        dlc_addr = REG_RXB1DLC;
        data_base = REG_RXB1D0;
    } else {
        return false;
    }

    uint8_t sidh = readRegister(base);
    uint8_t sidl = readRegister(base + 1);
    uint8_t dlc_reg = readRegister(dlc_addr);

    dlc = dlc_reg & 0x0F;
    extended = (sidl & 0x08) != 0;
    remote = (dlc_reg & 0x40) != 0;

    if (extended) {
        uint8_t eid8 = readRegister(base + 2);
        uint8_t eid0 = readRegister(base + 3);
        can_id = (sidh << 21) | (((sidl >> 5) & 0x07) << 18) |
                 ((sidl & 0x03) << 16) | (eid8 << 8) | eid0;
    } else {
        can_id = ((sidl >> 5) & 0x07) | (sidh << 3);
    }

    for (uint8_t i = 0; i < dlc && i < 8; ++i) {
        data[i] = readRegister(data_base + i);
    }

    bitModify(REG_CANINTF, 1 << buf, 0x00);
    return true;
}

bool MCP2515Driver::loopbackTest(uint32_t can_id, const uint8_t* data, uint8_t dlc)
{
    std::cout << "=== Loopback Test Start ===" << std::endl;

    reset();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    writeRegister(REG_CANCTRL, 0x80);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    BaudRateConfig cfg = BAUD_RATE_CONFIGS[2];
    for (size_t i = 0; i < BAUD_RATE_CONFIG_COUNT; ++i) {
        if (BAUD_RATE_CONFIGS[i].baud == bitrate_) {
            cfg = BAUD_RATE_CONFIGS[i];
            break;
        }
    }

    writeRegister(REG_CNF1, cfg.cnf1);
    writeRegister(REG_CNF2, cfg.cnf2);
    writeRegister(REG_CNF3, cfg.cnf3);
    writeRegister(REG_RXB0CTRL, 0x60);
    writeRegister(REG_CANINTF, 0x00);

    writeRegister(REG_CANCTRL, 0x40);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    uint8_t stat = readRegister(REG_CANSTAT);
    uint8_t mode = (stat >> 5) & 0x07;
    if (mode != 0x02) {
        std::cerr << "ERROR: Loopback mode setup failed, mode=" << (int)mode << std::endl;
        return false;
    }

    while (readRegister(REG_CANINTF) & 0x03) {
        uint32_t id;
        uint8_t d;
        uint8_t dlc_t;
        bool ext, rem;
        receiveCanFrame(id, &d, dlc_t, ext, rem);
    }

    uint8_t test_data[8] = {0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0};
    if (data != nullptr) {
        for (uint8_t i = 0; i < dlc && i < 8; ++i) {
            test_data[i] = data[i];
        }
    }

    std::cout << "TX: ID=0x" << std::hex << can_id << std::dec
              << " DLC=" << (int)dlc << " Data=[";
    for (uint8_t i = 0; i < dlc; ++i) {
        std::cout << "0x" << std::hex << (int)test_data[i] << std::dec;
        if (i < dlc - 1) std::cout << ", ";
    }
    std::cout << "]" << std::endl;

    if (!sendCanFrame(can_id, test_data, dlc, false, false)) {
        writeRegister(REG_CANCTRL, 0x00);
        return false;
    }

    for (int i = 0; i < 200; ++i) {
        uint32_t rx_id;
        uint8_t rx_data[8];
        uint8_t rx_dlc;
        bool rx_ext, rx_rem;
        if (receiveCanFrame(rx_id, rx_data, rx_dlc, rx_ext, rx_rem)) {
            std::cout << "RX: ID=0x" << std::hex << rx_id << std::dec
                      << " DLC=" << (int)rx_dlc << " Data=[";
            for (uint8_t j = 0; j < rx_dlc; ++j) {
                std::cout << "0x" << std::hex << (int)rx_data[j] << std::dec;
                if (j < rx_dlc - 1) std::cout << ", ";
            }
            std::cout << "]" << std::endl;

            if (rx_id == can_id && rx_dlc == dlc) {
                bool match = true;
                for (uint8_t j = 0; j < dlc; ++j) {
                    if (rx_data[j] != test_data[j]) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    writeRegister(REG_CANCTRL, 0x00);
                    std::cout << "OK: Loopback test passed" << std::endl;
                    return true;
                }
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    writeRegister(REG_CANCTRL, 0x00);
    std::cerr << "ERROR: Timeout - no matching frame received" << std::endl;
    return false;
}

void MCP2515Driver::setReceiveCallback(std::function<void(uint32_t, const uint8_t*, uint8_t, bool, bool)> callback)
{
    rx_callback_ = callback;
}

void MCP2515Driver::rxLoop()
{
    while (rx_thread_running_) {
        uint32_t can_id;
        uint8_t data[8];
        uint8_t dlc;
        bool extended, remote;

        if (receiveCanFrame(can_id, data, dlc, extended, remote)) {
            if (rx_callback_) {
                rx_callback_(can_id, data, dlc, extended, remote);
            }
        }

        uint8_t intf = readRegister(REG_CANINTF);
        if ((intf & 0x03) != 0) {
            if (receiveCanFrame(can_id, data, dlc, extended, remote)) {
                if (rx_callback_) {
                    rx_callback_(can_id, data, dlc, extended, remote);
                }
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

void MCP2515Driver::startRxThread()
{
    if (rx_thread_ == nullptr) {
        rx_thread_running_ = true;
        rx_thread_ = new std::thread(&MCP2515Driver::rxLoop, this);
    }
}

void MCP2515Driver::stopRxThread()
{
    if (rx_thread_ != nullptr) {
        rx_thread_running_ = false;
        if (rx_thread_->joinable()) {
            rx_thread_->join();
        }
        delete rx_thread_;
        rx_thread_ = nullptr;
    }
}