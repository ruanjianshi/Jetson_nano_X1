#include "../include/Logger.h"
#include "../tests/thread_management/ThreadTest.h"
#include "../tests/mutex/MutexTest.h"
#include "../tests/condition/ConditionTest.h"
#include "../tests/semaphore/SemaphoreTest.h"
#include "../tests/rwlock/RWLockTest.h"
#include "../tests/tls/TLSTest.h"

#include <iostream>
#include <chrono>

void printBanner() {
    std::cout << "\n";
    std::cout << "========================================\n";
    std::cout << "   C++ Multithreading Development Test\n";
    std::cout << "========================================\n";
    std::cout << "\n";
}

void printMenu() {
    std::cout << "\n=== Test Menu ===\n";
    std::cout << "1. Thread Management Tests\n";
    std::cout << "2. Mutex Tests\n";
    std::cout << "3. Condition Variable Tests\n";
    std::cout << "4. Semaphore Tests\n";
    std::cout << "5. Read-Write Lock Tests\n";
    std::cout << "6. Thread Local Storage Tests\n";
    std::cout << "7. Run All Tests\n";
    std::cout << "0. Exit\n";
    std::cout << "\nEnter your choice: ";
}

int main() {
    printBanner();
    
    Logger::getInstance().info("Multithreading Test Suite Started");
    
    std::stringstream ss;
    ss << "C++ Standard: " << __cplusplus;
    Logger::getInstance().info(ss.str());
    
    int choice;
    
    do {
        printMenu();
        std::cin >> choice;
        
        switch (choice) {
            case 1:
                ThreadManager::runAllTests();
                break;
            case 2:
                MutexTest::runAllTests();
                break;
            case 3:
                ConditionVariableTest::runAllTests();
                break;
            case 4:
                SemaphoreTest::runAllTests();
                break;
            case 5:
                ReadWriteLockTest::runAllTests();
                break;
            case 6:
                ThreadLocalStorageTest::runAllTests();
                break;
            case 7:
                ThreadManager::runAllTests();
                MutexTest::runAllTests();
                ConditionVariableTest::runAllTests();
                SemaphoreTest::runAllTests();
                ReadWriteLockTest::runAllTests();
                ThreadLocalStorageTest::runAllTests();
                break;
            case 0:
                Logger::getInstance().info("Exiting test suite");
                std::cout << "\nGoodbye!\n";
                break;
            default:
                std::cout << "Invalid choice. Please try again.\n";
        }
        
        if (choice != 0) {
            std::cout << "\nPress Enter to continue...";
            std::cin.ignore();
            std::cin.get();
        }
    } while (choice != 0);
    
    Logger::getInstance().info("Multithreading Test Suite Completed");
    
    return 0;
}