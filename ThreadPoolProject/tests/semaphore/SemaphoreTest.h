#pragma once

#include <thread>
#include <vector>
#include <mutex>
#include <condition_variable>
#include "Logger.h"

class Semaphore {
private:
    int count;
    std::mutex mtx;
    std::condition_variable cv;

public:
    Semaphore(int initial = 0) : count(initial) {}

    void acquire() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this] { return count > 0; });
        count--;
    }

    bool try_acquire() {
        std::unique_lock<std::mutex> lock(mtx);
        if (count > 0) {
            count--;
            return true;
        }
        return false;
    }

    void release() {
        std::lock_guard<std::mutex> lock(mtx);
        count++;
        cv.notify_one();
    }
};

class SemaphoreTest {
public:
    static void testCountingSemaphore() {
        TEST_START("Counting Semaphore");
        
        Semaphore sem(3);
        std::atomic<int> activeThreads(0);
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 6; ++i) {
            threads.emplace_back([&sem, &activeThreads, i]() {
                sem.acquire();
                
                int current = ++activeThreads;
                std::stringstream ss;
                ss << "Thread " << i << " entered, active: " << current;
                LOG_INFO(ss.str());
                
                std::this_thread::sleep_for(std::chrono::milliseconds(200));
                
                --activeThreads;
                ss.str("");
                ss << "Thread " << i << " leaving, active: " << activeThreads.load();
                LOG_INFO(ss.str());
                
                sem.release();
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_END("Counting Semaphore");
    }

    static void testBinarySemaphore() {
        TEST_START("Binary Semaphore");
        
        Semaphore sem(1);
        std::mutex mtx;
        int counter = 0;
        
        auto worker = [&sem, &mtx, &counter](int id) {
            for (int i = 0; i < 5; ++i) {
                sem.acquire();
                
                {
                    std::lock_guard<std::mutex> lock(mtx);
                    counter++;
                    std::stringstream ss;
                    ss << "Worker " << id << " incrementing counter to " << counter;
                    LOG_INFO(ss.str());
                }
                
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
                sem.release();
            }
        };
        
        std::thread t1(worker, 1);
        std::thread t2(worker, 2);
        
        t1.join();
        t2.join();
        
        std::stringstream ss;
        ss << "Final counter: " << counter;
        LOG_INFO(ss.str());
        
        TEST_END("Binary Semaphore");
    }

    static void testTryAcquire() {
        TEST_START("Semaphore Try Acquire");
        
        Semaphore sem(1);
        int successCount = 0;
        int failCount = 0;
        
        std::thread t1([&sem]() {
            sem.acquire();
            LOG_INFO("Thread 1 acquired semaphore");
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            sem.release();
            LOG_INFO("Thread 1 released semaphore");
        });
        
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        
        std::thread t2([&sem, &successCount, &failCount]() {
            for (int i = 0; i < 5; ++i) {
                if (sem.try_acquire()) {
                    successCount++;
                    std::stringstream ss;
                    ss << "Thread 2 try_acquire succeeded (attempt " << i + 1 << ")";
                    LOG_INFO(ss.str());
                    sem.release();
                } else {
                    failCount++;
                    std::stringstream ss;
                    ss << "Thread 2 try_acquire failed (attempt " << i + 1 << ")";
                    LOG_INFO(ss.str());
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(20));
            }
        });
        
        t1.join();
        t2.join();
        
        std::stringstream ss;
        ss << "Success: " << successCount << ", Failed: " << failCount;
        LOG_INFO(ss.str());
        
        TEST_END("Semaphore Try Acquire");
    }

    static void runAllTests() {
        LOG_INFO("\n\n=== Semaphore Tests ===\n");
        testCountingSemaphore();
        testBinarySemaphore();
        testTryAcquire();
        LOG_INFO("=== All Semaphore Tests Completed ===\n");
    }
};