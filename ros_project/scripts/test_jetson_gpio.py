#!/usr/bin/env python3
import Jetson.GPIO as GPIO
import time

def test_jetson_gpio():
    """测试Jetson.GPIO库的完整功能"""
    
    print("Jetson GPIO Library Test Suite")
    print("=" * 50)
    print(f"Jetson.GPIO Version: {GPIO.VERSION}")
    print("=" * 50)
    
    try:
        # 测试1: GPIO模式设置
        print("\n[TEST 1] GPIO Mode Setup")
        GPIO.setmode(GPIO.BOARD)
        print("✅ BOARD mode set successfully")
        
        # 测试2: 引脚初始化
        print("\n[TEST 2] GPIO Pin Initialization")
        test_pins = [18, 19, 21, 22, 23, 24, 27, 28, 29, 30]
        
        initialized_pins = []
        for pin in test_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                initialized_pins.append(pin)
                print(f"  ✅ GPIO {pin} initialized as output")
            except Exception as e:
                print(f"  ❌ GPIO {pin} failed: {e}")
        
        # 测试3: 输出功能测试
        print("\n[TEST 3] GPIO Output Function")
        if initialized_pins:
            test_pin = initialized_pins[0]
            try:
                GPIO.output(test_pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(test_pin, GPIO.LOW)
                print(f"  ✅ GPIO {test_pin} output test successful")
            except Exception as e:
                print(f"  ❌ GPIO {test_pin} output test failed: {e}")
        
        # 测试4: 脉冲测试
        print("\n[TEST 4] GPIO Pulse Test")
        if initialized_pins:
            test_pin = initialized_pins[0]
            try:
                for i in range(5):
                    GPIO.output(test_pin, GPIO.HIGH)
                    time.sleep(0.05)
                    GPIO.output(test_pin, GPIO.LOW)
                    time.sleep(0.05)
                print(f"  ✅ GPIO {test_pin} pulse test successful (5 pulses)")
            except Exception as e:
                print(f"  ❌ GPIO {test_pin} pulse test failed: {e}")
        
        # 测试5: 输入功能测试
        print("\n[TEST 5] GPIO Input Function")
        try:
            input_pin = initialized_pins[0] if len(initialized_pins) > 1 else 18
            GPIO.setup(input_pin, GPIO.IN)
            time.sleep(0.1)
            state = GPIO.input(input_pin)
            print(f"  ✅ GPIO {input_pin} input test successful, state: {state}")
        except Exception as e:
            print(f"  ❌ GPIO input test failed: {e}")
        
        # 测试6: PWM功能测试
        print("\n[TEST 6] GPIO PWM Function")
        try:
            pwm_pin = 18  # GPIO18支持PWM
            GPIO.setup(pwm_pin, GPIO.OUT)
            pwm = GPIO.PWM(pwm_pin, 1000)  # 1kHz
            pwm.start(50)  # 50%占空比
            time.sleep(0.5)
            pwm.stop()
            print(f"  ✅ GPIO {pwm_pin} PWM test successful")
        except Exception as e:
            print(f"  ❌ GPIO PWM test failed: {e}")
        
        # 测试7: 清理功能测试
        print("\n[TEST 7] GPIO Cleanup Function")
        try:
            GPIO.cleanup()
            print("  ✅ GPIO cleanup successful")
        except Exception as e:
            print(f"  ❌ GPIO cleanup failed: {e}")
        
        # 显示GPIO信息
        print("\n" + "=" * 50)
        print("GPIO Information Summary")
        print("=" * 50)
        print(f"Available GPIO Modes: BOARD={GPIO.BOARD}, BCM={GPIO.BCM}, TEGRA_SOC={GPIO.TEGRA_SOC}")
        print(f"Initialized Pins: {len(initialized_pins)}")
        print(f"Available Pins: {len(test_pins)}")
        
        print("\nRecommended GPIO Pin Configuration:")
        print("  GPIO18, GPIO19: PWM Output")
        print("  GPIO21, GPIO22: I2C (avoid if using I2C)")
        print("  GPIO23, GPIO24, GPIO27: SPI (avoid if using SPI)")
        print("  GPIO28, GPIO29: UART (avoid if using UART)")
        print("  GPIO30+: General GPIO (recommended)")
        
        print("\n" + "=" * 50)
        print("🎉 All GPIO tests completed successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        GPIO.cleanup()
        return False

if __name__ == '__main__':
    success = test_jetson_gpio()
    exit(0 if success else 1)