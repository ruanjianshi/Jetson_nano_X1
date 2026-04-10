#pragma once

#include <condition_variable>
#include <mutex>
#include <thread>
#include <queue>
#include <atomic>
#include "Logger.h"

class ConditionVariableTest {
private:
    static std::mutex mtx;
    static std::condition_variable cv;
    static bool ready;
    static std::queue<int> taskQueue;

public:
    static void testBasicCondition() {
        TEST_START("Basic Condition Variable");
        
        ready = false;
        
        std::thread worker([]() {
            LOG_INFO("Worker waiting for signal");
            std::unique_lock<std::mutex> lock(mtx);
            cv.wait(lock, []{ return ready; });
            LOG_INFO("Worker received signal");
        });
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        {
            std::lock_guard<std::mutex> lock(mtx);
            ready = true;
            LOG_INFO("Main thread setting ready flag");
        }
        
        cv.notify_one();
        worker.join();
        
        TEST_END("Basic Condition Variable");
    }

    static void testNotifyAll() {
        TEST_START("Notify All");
        
        ready = false;
        const int numWorkers = 3;
        std::vector<std::thread> workers;
        
        for (int i = 0; i < numWorkers; ++i) {
            workers.emplace_back([i]() {
                std::unique_lock<std::mutex> lock(mtx);
                std::stringstream ss;
                ss << "Worker " << i << " waiting";
                LOG_INFO(ss.str());
                
                cv.wait(lock, []{ return ready; });
                
                ss.str("");
                ss << "Worker " << i << " awakened";
                LOG_INFO(ss.str());
            });
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        {
            std::lock_guard<std::mutex> lock(mtx);
            ready = true;
            LOG_INFO("Main thread notifying all workers");
        }
        
        cv.notify_all();
        
        for (auto& w : workers) {
            w.join();
        }
        
        TEST_END("Notify All");
    }

    static void testProducerConsumer() {
        TEST_START("Producer Consumer Pattern");
        
        taskQueue = std::queue<int>();
        std::atomic<bool> done{false};
        
        auto producer = [&done]() {
            for (int i = 1; i <= 5; ++i) {
                {
                    std::lock_guard<std::mutex> lock(mtx);
                    taskQueue.push(i);
                    std::stringstream ss;
                    ss << "Produced: " << i;
                    LOG_INFO(ss.str());
                }
                cv.notify_one();
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
            }
            
            {
                std::lock_guard<std::mutex> lock(mtx);
                done = true;
                LOG_INFO("Producer done");
            }
            cv.notify_all();
        };
        
        auto consumer = [&done]() {
            while (true) {
                std::unique_lock<std::mutex> lock(mtx);
                cv.wait(lock, [&done] {
                    return !taskQueue.empty() || done;
                });
                
                if (taskQueue.empty() && done) {
                    LOG_INFO("Consumer finished");
                    break;
                }
                
                if (!taskQueue.empty()) {
                    int item = taskQueue.front();
                    taskQueue.pop();
                    std::stringstream ss;
                    ss << "Consumed: " << item;
                    LOG_INFO(ss.str());
                }
            }
        };
        
        std::thread t1(producer);
        std::thread t2(consumer);
        
        t1.join();
        t2.join();
        
        TEST_END("Producer Consumer Pattern");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Condition Variable Tests ===\n");
        testBasicCondition();
        testNotifyAll();
        testProducerConsumer();
        LOG_INFO("=== All Condition Variable Tests Completed ===\n");
    }
};

std::mutex ConditionVariableTest::mtx;
std::condition_variable ConditionVariableTest::cv;
bool ConditionVariableTest::ready = false;
std::queue<int> ConditionVariableTest::taskQueue;