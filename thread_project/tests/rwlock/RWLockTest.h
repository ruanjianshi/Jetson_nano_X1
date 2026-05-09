#pragma once

#include <shared_mutex>
#include <thread>
#include <vector>
#include <atomic>
#include "Logger.h"

class ReadWriteLockTest {
private:
    static int sharedData;
    static std::shared_mutex rwMtx;

public:
    static void testMultipleReaders() {
        TEST_START("Multiple Readers");
        
        sharedData = 0;
        
        auto reader = [](int id) {
            std::shared_lock<std::shared_mutex> lock(rwMtx);
            std::stringstream ss;
            ss << "Reader " << id << " reading data: " << sharedData;
            LOG_INFO(ss.str());
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            ss.str("");
            ss << "Reader " << id << " finished reading";
            LOG_INFO(ss.str());
        };
        
        std::vector<std::thread> readers;
        
        LOG_INFO("Starting 5 readers simultaneously");
        
        for (int i = 0; i < 5; ++i) {
            readers.emplace_back(reader, i);
        }
        
        for (auto& t : readers) {
            t.join();
        }
        
        TEST_END("Multiple Readers");
    }

    static void testWriterExclusive() {
        TEST_START("Writer Exclusive Access");
        
        sharedData = 0;
        
        auto writer = [](int id, int value) {
            std::unique_lock<std::shared_mutex> lock(rwMtx);
            std::stringstream ss;
            ss << "Writer " << id << " writing data: " << value;
            LOG_INFO(ss.str());
            
            sharedData = value;
            std::this_thread::sleep_for(std::chrono::milliseconds(150));
            
            ss.str("");
            ss << "Writer " << id << " finished writing";
            LOG_INFO(ss.str());
        };
        
        auto reader = [](int id) {
            std::shared_lock<std::shared_mutex> lock(rwMtx);
            std::stringstream ss;
            ss << "Reader " << id << " reading data: " << sharedData;
            LOG_INFO(ss.str());
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        };
        
        std::vector<std::thread> threads;
        
        threads.emplace_back(writer, 1, 100);
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        
        for (int i = 0; i < 3; ++i) {
            threads.emplace_back(reader, i);
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        threads.emplace_back(writer, 2, 200);
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_END("Writer Exclusive Access");
    }

    static void testReadersWriterConflict() {
        TEST_START("Reader-Writer Conflict");
        
        sharedData = 0;
        std::atomic<int> readerCount(0);
        std::atomic<int> writerCount(0);
        
        auto reader = [&](int id) {
            std::shared_lock<std::shared_mutex> lock(rwMtx);
            int currentReaders = ++readerCount;
            std::stringstream ss;
            ss << "Reader " << id << " entered, active readers: " << currentReaders;
            LOG_INFO(ss.str());
            
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            
            --readerCount;
            ss.str("");
            ss << "Reader " << id << " leaving, data: " << sharedData;
            LOG_INFO(ss.str());
        };
        
        auto writer = [&](int id) {
            std::unique_lock<std::shared_mutex> lock(rwMtx);
            int currentWriters = ++writerCount;
            std::stringstream ss;
            ss << "Writer " << id << " entered, active writers: " << currentWriters;
            LOG_INFO(ss.str());
            
            sharedData = id * 10;
            std::this_thread::sleep_for(std::chrono::milliseconds(80));
            
            --writerCount;
            ss.str("");
            ss << "Writer " << id << " leaving, data: " << sharedData;
            LOG_INFO(ss.str());
        };
        
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 4; ++i) {
            threads.emplace_back(reader, i);
        }
        
        for (int i = 0; i < 2; ++i) {
            threads.emplace_back(writer, i + 1);
        }
        
        for (int i = 4; i < 6; ++i) {
            threads.emplace_back(reader, i);
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_END("Reader-Writer Conflict");
    }

    static void testTryLock() {
        TEST_START("Read-Write Try Lock");
        
        sharedData = 0;
        
        std::thread t1([&]() {
            std::unique_lock<std::shared_mutex> lock(rwMtx);
            LOG_INFO("Thread 1 acquired write lock");
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            LOG_INFO("Thread 1 releasing write lock");
        });
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        
        std::thread t2([&]() {
            if (rwMtx.try_lock_shared()) {
                LOG_INFO("Thread 2 acquired read lock (unexpected!)");
                rwMtx.unlock_shared();
            } else {
                LOG_INFO("Thread 2 failed to acquire read lock (expected)");
            }
            
            if (rwMtx.try_lock()) {
                LOG_INFO("Thread 2 acquired write lock (unexpected!)");
                rwMtx.unlock();
            } else {
                LOG_INFO("Thread 2 failed to acquire write lock (expected)");
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
            if (rwMtx.try_lock_shared()) {
                LOG_INFO("Thread 2 acquired read lock (expected)");
                rwMtx.unlock_shared();
            }
        });
        
        t1.join();
        t2.join();
        
        TEST_END("Read-Write Try Lock");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Read-Write Lock Tests ===\n");
        testMultipleReaders();
        testWriterExclusive();
        testReadersWriterConflict();
        testTryLock();
        LOG_INFO("=== All Read-Write Lock Tests Completed ===\n");
    }
};

int ReadWriteLockTest::sharedData = 0;
std::shared_mutex ReadWriteLockTest::rwMtx;