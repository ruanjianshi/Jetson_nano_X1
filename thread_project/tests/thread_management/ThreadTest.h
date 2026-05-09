#pragma once

#include <thread>
#include <vector>
#include <atomic>
#include <functional>
#include "Logger.h"

class ThreadManager {
public:
    static void testBasicThreadCreation() {
        TEST_START("Basic Thread Creation");
        
        std::thread t([]() {
            LOG_INFO("Worker thread running");
        });
        
        LOG_INFO("Main thread waiting for worker");
        t.join();
        
        LOG_INFO("Worker thread finished");
        TEST_END("Basic Thread Creation");
    }

    static void testGetThreadId() {
        TEST_START("Get Thread ID");
        
        std::thread t([]() {
            std::thread::id thisId = std::this_thread::get_id();
            std::stringstream ss;
            ss << "Worker thread ID: " << thisId;
            LOG_INFO(ss.str());
        });
        
        std::thread::id mainId = std::this_thread::get_id();
        std::stringstream ss;
        ss << "Main thread ID: " << mainId;
        LOG_INFO(ss.str());
        
        t.join();
        TEST_END("Get Thread ID");
    }

    static void testThreadWithReturn() {
        TEST_START("Thread With Return Value");
        
        std::atomic<int> result(0);
        std::thread t([&result]() {
            result = 42;
            LOG_INFO("Worker computed result: 42");
        });
        
        t.join();
        
        std::stringstream ss;
        ss << "Result from worker: " << result.load();
        LOG_INFO(ss.str());
        
        TEST_END("Thread With Return Value");
    }

    static void testDetachThread() {
        TEST_START("Detached Thread");
        
        std::thread t([]() {
            LOG_INFO("Detached thread running");
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            LOG_INFO("Detached thread finishing");
        });
        
        t.detach();
        LOG_INFO("Thread detached from main");
        
        std::this_thread::sleep_for(std::chrono::milliseconds(150));
        LOG_INFO("Main thread continuing");
        
        TEST_END("Detached Thread");
    }

    static void testMultipleThreads() {
        TEST_START("Multiple Threads");
        
        const int numThreads = 5;
        std::vector<std::thread> threads;
        
        for (int i = 0; i < numThreads; ++i) {
            threads.emplace_back([i]() {
                std::stringstream ss;
                ss << "Thread " << i << " started";
                LOG_INFO(ss.str());
                
                std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
                
                ss.str("");
                ss << "Thread " << i << " finished";
                LOG_INFO(ss.str());
            });
        }
        
        LOG_INFO("Waiting for all threads");
        
        for (auto& t : threads) {
            t.join();
        }
        
        LOG_INFO("All threads completed");
        TEST_END("Multiple Threads");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Thread Management Tests ===\n");
        testBasicThreadCreation();
        testGetThreadId();
        testThreadWithReturn();
        testDetachThread();
        testMultipleThreads();
        LOG_INFO("=== All Thread Management Tests Completed ===\n");
    }
};