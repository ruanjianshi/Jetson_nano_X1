.PHONY: all clean run test help

all:
	@mkdir -p build logs
	@cd build && cmake .. && make
	@echo "Build complete. Run with: make run"

clean:
	@rm -rf build
	@rm -f logs/*.log
	@echo "Cleaned build and log files"

run: all
	@./build/multithread_test

test: all
	@echo "Running all tests..."
	@echo "7" | ./build/multithread_test

help:
	@echo "Available targets:"
	@echo "  all   - Build the project"
	@echo "  clean - Remove build and log files"
	@echo "  run   - Build and run the interactive test"
	@echo "  test  - Run all tests automatically"
	@echo "  help  - Show this help message"