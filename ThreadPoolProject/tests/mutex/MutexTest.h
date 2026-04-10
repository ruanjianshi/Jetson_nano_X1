#pragma once

#include <mutex>
#include <vector>
#include <thread>
#include "Logger.h"

class MutexTest {
private:
    static int counter;
    static std::mutex mtx;

public:
    static void testBasicMutex() {
        TEST_START("Basic Mutex");
        
        counter = 0;
        const int numThreads = 10;
        std::vector<std::thread> threads;
        
        for (int i = 0; i < numThreads; ++i) {
            threads.emplace_back([]() {
                for (int j = 0; j < 100; ++j) {
                    mtx.lock();
                    counter++;
                    mtx.unlock();
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        std::stringstream ss;
        ss << "Final counter value: " << counter;
        LOG_INFO(ss.str());
        
        TEST_END("Basic Mutex");
    }

    static void testLockGuard() {
        TEST_START("Lock Guard");
        
        counter = 0;
        const int numThreads = 10;
        std::vector<std::thread> threads;
        
        for (int i = 0; i < numThreads; ++i) {
            threads.emplace_back([]() {
                for (int j = 0; j < 100; ++j) {
                    std::lock_guard<std::mutex> lock(mtx);
                    counter++;
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        std::stringstream ss;
        ss << "Final counter value: " << counter;
        LOG_INFO(ss.str());
        
        TEST_END("Lock Guard");
    }

    static void testUniqueLock() {
        TEST_START("Unique Lock");
        
        counter = 0;
        const int numThreads = 10;
        std::vector<std::thread> threads;
        
        for (int i = 0; i < numThreads; ++i) {
            threads.emplace_back([]() {
                for (int j = 0; j < 100; ++j) {
                    std::unique_lock<std::mutex> lock(mtx);
                    counter++;
                    lock.unlock();
                    std::this_thread::sleep_for(std::chrono::microseconds(10));
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        std::stringstream ss;
        ss << "Final counter value: " << counter;
        LOG_INFO(ss.str());
        
        TEST_END("Unique Lock");
    }

    static void testTryLock() {
        TEST_START("Try Lock");
        
        int successCount = 0;
        int failCount = 0;
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 5; ++i) {
            threads.emplace_back([&successCount, &failCount]() {
                for (int j = 0; j < 10; ++j) {
                    if (mtx.try_lock()) {
                        successCount++;
                        mtx.unlock();
                    } else {
                        failCount++;
                    }
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        std::stringstream ss;
        ss << "Try lock success: " << successCount << ", failed: " << failCount;
        LOG_INFO(ss.str());
        
        TEST_END("Try Lock");
    }

    static void testRecursiveMutex() {
        TEST_START("Recursive Mutex");
        
        std::recursive_mutex recMtx;
        int depth = 0;
        
        std::thread t([&recMtx, &depth]() {
            std::lock_guard<std::recursive_mutex> lock1(recMtx);
            depth++;
            std::stringstream ss;
            ss << "Depth 1: " << depth;
            LOG_INFO(ss.str());
            
            {
                std::lock_guard<std::recursive_mutex> lock2(recMtx);
                depth++;
                ss.str("");
                ss << "Depth 2: " << depth;
                LOG_INFO(ss.str());
            }
            
            depth--;
            LOG_INFO("Back to depth 1");
        });
        
        t.join();
        
        TEST_END("Recursive Mutex");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Mutex Tests ===\n");
        testBasicMutex();
        testLockGuard();
        testUniqueLock();
        testTryLock();
        testRecursiveMutex();
        LOG_INFO("=== All Mutex Tests Completed ===\n");
    }
};

int MutexTest::counter = 0;
std::mutex MutexTest::mtx;