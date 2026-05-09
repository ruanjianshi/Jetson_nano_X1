#pragma once

#include <thread>
#include <vector>
#include "Logger.h"

class ThreadLocalStorageTest {
public:
    static void testThreadLocal() {
        TEST_START("Thread Local Storage");
        
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 5; ++i) {
            threads.emplace_back([i]() {
                thread_local int var = 0;
                
                for (int j = 0; j < 3; ++j) {
                    var++;
                    std::stringstream ss;
                    ss << "Thread " << i << " iteration " << j + 1 
                       << ", local var: " << var;
                    LOG_INFO(ss.str());
                    std::this_thread::sleep_for(std::chrono::milliseconds(50));
                }
                
                std::stringstream ss;
                ss << "Thread " << i << " final local var: " << var;
                LOG_INFO(ss.str());
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_END("Thread Local Storage");
    }

    static void testTLSWithClasses() {
        TEST_START("TLS with Classes");
        
        class ThreadLocalCounter {
        public:
            ThreadLocalCounter() : count(0) {
                LOG_INFO("ThreadLocalCounter constructed");
            }
            
            ~ThreadLocalCounter() {
                std::stringstream ss;
                ss << "ThreadLocalCounter destroyed, count: " << count;
                LOG_INFO(ss.str());
            }
            
            void increment() {
                count++;
            }
            
            int getCount() const {
                return count;
            }
            
        private:
            int count;
        };
        
        thread_local ThreadLocalCounter counter;
        
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 4; ++i) {
            threads.emplace_back([i]() {
                thread_local ThreadLocalCounter localCounter;
                
                for (int j = 0; j < 5; ++j) {
                    localCounter.increment();
                    std::stringstream ss;
                    ss << "Thread " << i << " count: " << localCounter.getCount();
                    LOG_INFO(ss.str());
                    std::this_thread::sleep_for(std::chrono::milliseconds(30));
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_END("TLS with Classes");
    }

    static void testTLSVsGlobal() {
        TEST_START("TLS vs Global Variable");
        
        int globalVar = 0;
        
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 5; ++i) {
            threads.emplace_back([i, &globalVar]() {
                thread_local int localVar = 0;
                
                for (int j = 0; j < 3; ++j) {
                    localVar++;
                    globalVar++;
                    
                    std::stringstream ss;
                    ss << "Thread " << i << ": local=" << localVar 
                       << ", global=" << globalVar;
                    LOG_INFO(ss.str());
                    
                    std::this_thread::sleep_for(std::chrono::milliseconds(50));
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        std::stringstream ss;
        ss << "Final global variable: " << globalVar;
        LOG_INFO(ss.str());
        
        TEST_END("TLS vs Global Variable");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Thread Local Storage Tests ===\n");
        testThreadLocal();
        testTLSWithClasses();
        testTLSVsGlobal();
        LOG_INFO("=== All Thread Local Storage Tests Completed ===\n");
    }
};