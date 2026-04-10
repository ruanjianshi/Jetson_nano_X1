#!/usr/bin/env python3
"""
Jetson Nano B01 GPIO Information Query Script
查询并显示Jetson Nano B01 40引脚GPIO的分布和功能
"""

import Jetson.GPIO as GPIO
import sys

class JetsonGPIOInfo:
    """Jetson Nano GPIO信息查询类"""
    
    JETSON_NANO_PINOUT = {
        # 物理引脚编号: {信息字典}
        1: {'name': '3.3V', 'type': 'Power', 'function': '3.3V Power', 'bcm': None, 'mode': 'Power'},
        2: {'name': '5V', 'type': 'Power', 'function': '5V Power', 'bcm': None, 'mode': 'Power'},
        3: {'name': 'GPIO2', 'type': 'GPIO', 'function': 'I2C_SDA_1', 'bcm': 2, 'mode': 'I2C', 'board': 3},
        4: {'name': '5V', 'type': 'Power', 'function': '5V Power', 'bcm': None, 'mode': 'Power'},
        5: {'name': 'GPIO3', 'type': 'GPIO', 'function': 'I2C_SCL_1', 'bcm': 3, 'mode': 'I2C', 'board': 5},
        6: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        7: {'name': 'GPIO4', 'type': 'GPIO', 'function': 'GPIO_GPCLK0', 'bcm': 4, 'mode': 'GPIO', 'board': 7},
        8: {'name': 'GPIO14', 'type': 'GPIO', 'function': 'UART_TXD0', 'bcm': 14, 'mode': 'UART', 'board': 8},
        9: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        10: {'name': 'GPIO15', 'type': 'GPIO', 'function': 'UART_RXD0', 'bcm': 15, 'mode': 'UART', 'board': 10},
        11: {'name': 'GPIO17', 'type': 'GPIO', 'function': 'GPIO_GEN0', 'bcm': 17, 'mode': 'GPIO', 'board': 11},
        12: {'name': 'GPIO18', 'type': 'GPIO', 'function': 'GPIO_GEN1 / PWM0', 'bcm': 18, 'mode': 'GPIO/PWM', 'board': 12},
        13: {'name': 'GPIO27', 'type': 'GPIO', 'function': 'GPIO_GEN2', 'bcm': 27, 'mode': 'GPIO', 'board': 13},
        14: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        15: {'name': 'GPIO22', 'type': 'GPIO', 'function': 'GPIO_GEN3', 'bcm': 22, 'mode': 'GPIO', 'board': 15},
        16: {'name': 'GPIO23', 'type': 'GPIO', 'function': 'GPIO_GEN4', 'bcm': 23, 'mode': 'GPIO', 'board': 16},
        17: {'name': '3.3V', 'type': 'Power', 'function': '3.3V Power', 'bcm': None, 'mode': 'Power'},
        18: {'name': 'GPIO24', 'type': 'GPIO', 'function': 'GPIO_GEN5', 'bcm': 24, 'mode': 'GPIO', 'board': 18},
        19: {'name': 'GPIO10', 'type': 'GPIO', 'function': 'SPI_MOSI', 'bcm': 10, 'mode': 'SPI', 'board': 19},
        20: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        21: {'name': 'GPIO9', 'type': 'GPIO', 'function': 'SPI_MISO', 'bcm': 9, 'mode': 'SPI', 'board': 21},
        22: {'name': 'GPIO25', 'type': 'GPIO', 'function': 'GPIO_GEN6', 'bcm': 25, 'mode': 'GPIO', 'board': 22},
        23: {'name': 'GPIO11', 'type': 'GPIO', 'function': 'SPI_SCLK', 'bcm': 11, 'mode': 'SPI', 'board': 23},
        24: {'name': 'GPIO8', 'type': 'GPIO', 'function': 'SPI_CE0_N', 'bcm': 8, 'mode': 'SPI', 'board': 24},
        25: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        26: {'name': 'GPIO7', 'type': 'GPIO', 'function': 'SPI_CE1_N', 'bcm': 7, 'mode': 'SPI', 'board': 26},
        27: {'name': 'ID_SD', 'type': 'EEPROM', 'function': 'ID_SD (EEPROM)', 'bcm': 0, 'mode': 'I2C', 'board': 27},
        28: {'name': 'ID_SC', 'type': 'EEPROM', 'function': 'ID_SC (EEPROM)', 'bcm': 1, 'mode': 'I2C', 'board': 28},
        29: {'name': 'GPIO5', 'type': 'GPIO', 'function': 'GPIO_GEN7', 'bcm': 5, 'mode': 'GPIO', 'board': 29},
        30: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        31: {'name': 'GPIO6', 'type': 'GPIO', 'function': 'GPIO_GEN8', 'bcm': 6, 'mode': 'GPIO', 'board': 31},
        32: {'name': 'GPIO12', 'type': 'GPIO', 'function': 'GPIO_GEN9 / PWM0', 'bcm': 12, 'mode': 'GPIO/PWM', 'board': 32},
        33: {'name': 'GPIO13', 'type': 'GPIO', 'function': 'GPIO_GEN10 / PWM1', 'bcm': 13, 'mode': 'GPIO/PWM', 'board': 33},
        34: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        35: {'name': 'GPIO19', 'type': 'GPIO', 'function': 'GPIO_GEN11 / PWM1', 'bcm': 19, 'mode': 'GPIO/PWM', 'board': 35},
        36: {'name': 'GPIO16', 'type': 'GPIO', 'function': 'GPIO_GEN12', 'bcm': 16, 'mode': 'GPIO', 'board': 36},
        37: {'name': 'GPIO26', 'type': 'GPIO', 'function': 'GPIO_GEN13', 'bcm': 26, 'mode': 'GPIO', 'board': 37},
        38: {'name': 'GPIO20', 'type': 'GPIO', 'function': 'GPIO_GEN14', 'bcm': 20, 'mode': 'GPIO', 'board': 38},
        39: {'name': 'GND', 'type': 'Ground', 'function': 'Ground', 'bcm': None, 'mode': 'Ground'},
        40: {'name': 'GPIO21', 'type': 'GPIO', 'function': 'GPIO_GEN15', 'bcm': 21, 'mode': 'GPIO', 'board': 40}
    }
    
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        
    def display_pinout(self):
        """显示40引脚完整分布"""
        print("\n" + "="*80)
        print("Jetson Nano B01 40-Pin GPIO Pinout Information")
        print("Jetson Nano B01 40引脚GPIO分布信息")
        print("="*80)
        
        # 按列显示引脚分布（左右两列）
        for row in range(1, 21):
            left_pin = row
            right_pin = row + 20
            
            left_info = self.JETSON_NANO_PINOUT[left_pin]
            right_info = self.JETSON_NANO_PINOUT[right_pin]
            
            # 左侧引脚信息
            left_str = f"{left_pin:2d}: {left_info['name']:10s} | {left_info['type']:8s} | {left_info['function']:20s}"
            if left_info.get('bcm') is not None:
                left_str += f" | BCM{left_info['bcm']:2d}"
            
            # 右侧引脚信息
            right_str = f"{right_pin:2d}: {right_info['name']:10s} | {right_info['type']:8s} | {right_info['function']:20s}"
            if right_info.get('bcm') is not None:
                right_str += f" | BCM{right_info['bcm']:2d}"
            
            print(f"  {left_str}  ||  {right_str}")
        
        print("="*80 + "\n")
        
    def display_gpio_summary(self):
        """显示GPIO功能分类摘要"""
        print("="*80)
        print("GPIO Function Summary / GPIO功能分类摘要")
        print("="*80)
        
        # 统计各种功能的GPIO
        gpio_pins = []
        i2c_pins = []
        spi_pins = []
        uart_pins = []
        pwm_pins = []
        power_pins = []
        ground_pins = []
        eeprom_pins = []
        
        for pin_num, pin_info in self.JETSON_NANO_PINOUT.items():
            pin_type = pin_info['type']
            mode = pin_info['mode']
            
            if pin_type == 'GPIO':
                gpio_pins.append((pin_num, pin_info))
                if 'I2C' in mode:
                    i2c_pins.append((pin_num, pin_info))
                elif 'SPI' in mode:
                    spi_pins.append((pin_num, pin_info))
                elif 'UART' in mode:
                    uart_pins.append((pin_num, pin_info))
                elif 'PWM' in mode:
                    pwm_pins.append((pin_num, pin_info))
            elif pin_type == 'Power':
                power_pins.append((pin_num, pin_info))
            elif pin_type == 'Ground':
                ground_pins.append((pin_num, pin_info))
            elif pin_type == 'EEPROM':
                eeprom_pins.append((pin_num, pin_info))
        
        # 显示分类统计
        print(f"Total Pins: 40")
        print(f"GPIO Pins: {len(gpio_pins)} (可用GPIO引脚)")
        print(f"Power Pins: {len(power_pins)} (电源引脚)")
        print(f"Ground Pins: {len(ground_pins)} (地线引脚)")
        print(f"EEPROM Pins: {len(eeprom_pins)} (EEPROM ID引脚)")
        print()
        
        # 显示详细分类
        self._display_pin_list("General GPIO (通用GPIO)", [p for p in gpio_pins if p[1]['mode'] == 'GPIO'])
        self._display_pin_list("I2C (I2C总线)", i2c_pins)
        self._display_pin_list("SPI (SPI总线)", spi_pins)
        self._display_pin_list("UART (串口通信)", uart_pins)
        self._display_pin_list("PWM (脉冲宽度调制)", pwm_pins)
        self._display_pin_list("Power (电源)", power_pins)
        self._display_pin_list("Ground (地线)", ground_pins)
        self._display_pin_list("EEPROM (EEPROM ID)", eeprom_pins)
        
        print("="*80 + "\n")
        
    def _display_pin_list(self, category, pins):
        """显示特定分类的引脚列表"""
        if not pins:
            return
            
        print(f"{category}:")
        for pin_num, pin_info in pins:
            bcm = f"BCM{pin_info['bcm']}" if pin_info.get('bcm') else "N/A"
            print(f"  Pin {pin_num:2d} ({pin_info['name']:10s}) | {pin_info['function']:25s} | {bcm}")
        print()
        
    def display_pin_details(self, pin_numbers=None):
        """显示指定引脚的详细信息"""
        if pin_numbers is None:
            pin_numbers = list(self.JETSON_NANO_PINOUT.keys())
        
        print("="*80)
        print("Detailed Pin Information / 详细引脚信息")
        print("="*80)
        
        for pin_num in pin_numbers:
            if pin_num not in self.JETSON_NANO_PINOUT:
                print(f"Pin {pin_num}: Invalid pin number")
                continue
                
            pin_info = self.JETSON_NANO_PINOUT[pin_num]
            
            print(f"\nPin {pin_num}:")
            print(f"  Name: {pin_info['name']}")
            print(f"  Type: {pin_info['type']}")
            print(f"  Function: {pin_info['function']}")
            print(f"  Mode: {pin_info['mode']}")
            
            if pin_info.get('bcm') is not None:
                print(f"  BCM Number: {pin_info['bcm']}")
                
            # 尝试读取当前GPIO状态（仅对GPIO引脚有效）
            if pin_info['type'] == 'GPIO':
                try:
                    GPIO.setup(pin_num, GPIO.IN)
                    state = GPIO.input(pin_num)
                    print(f"  Current State: {'HIGH' if state else 'LOW'}")
                    GPIO.cleanup(pin_num)
                except:
                    print(f"  Current State: Unable to read")
        
        print("\n" + "="*80 + "\n")
        
    def display_available_gpio(self):
        """显示可用的GPIO引脚（排除特殊功能引脚）"""
        print("="*80)
        print("Available GPIO Pins (Recommended for General Use)")
        print("可用GPIO引脚（推荐用于一般用途）")
        print("="*80)
        
        available_pins = []
        for pin_num, pin_info in self.JETSON_NANO_PINOUT.items():
            if pin_info['type'] == 'GPIO' and pin_info['mode'] == 'GPIO':
                available_pins.append((pin_num, pin_info))
        
        for pin_num, pin_info in available_pins:
            print(f"  Pin {pin_num:2d} ({pin_info['name']:10s}) | BCM{pin_info['bcm']:2d}")
        
        print(f"\nTotal available GPIO pins: {len(available_pins)}")
        print("="*80 + "\n")
        
    def display_power_distribution(self):
        """显示电源分布信息"""
        print("="*80)
        print("Power Distribution / 电源分布")
        print("="*80)
        
        power_3v3 = [p for p in self.JETSON_NANO_PINOUT.values() if p['type'] == 'Power' and '3.3' in p['function']]
        power_5v = [p for p in self.JETSON_NANO_PINOUT.values() if p['type'] == 'Power' and '5V' in p['function']]
        ground = [p for p in self.JETSON_NANO_PINOUT.values() if p['type'] == 'Ground']
        
        print(f"3.3V Power Pins: {len(power_3v3)}")
        for i, pin_info in enumerate(power_3v3, 1):
            pin_num = next(k for k, v in self.JETSON_NANO_PINOUT.items() if v == pin_info)
            print(f"  Pin {pin_num}")
        
        print(f"\n5V Power Pins: {len(power_5v)}")
        for i, pin_info in enumerate(power_5v, 1):
            pin_num = next(k for k, v in self.JETSON_NANO_PINOUT.items() if v == pin_info)
            print(f"  Pin {pin_num}")
        
        print(f"\nGround Pins: {len(ground)}")
        for i, pin_info in enumerate(ground, 1):
            pin_num = next(k for k, v in self.JETSON_NANO_PINOUT.items() if v == pin_info)
            print(f"  Pin {pin_num}")
        
        print("="*80 + "\n")
        
    def cleanup(self):
        GPIO.cleanup()

def main():
    """主函数"""
    print("\n" + "="*80)
    print("Jetson Nano B01 GPIO Information Query Tool")
    print("Jetson Nano B01 GPIO信息查询工具")
    print("="*80 + "\n")
    
    gpio_info = JetsonGPIOInfo()
    
    while True:
        print("Please select an option (请选择选项):")
        print("1. Display full 40-pin pinout (显示完整40引脚分布)")
        print("2. Display GPIO function summary (显示GPIO功能分类摘要)")
        print("3. Display available GPIO pins (显示可用GPIO引脚)")
        print("4. Display power distribution (显示电源分布)")
        print("5. Display detailed info for specific pins (显示特定引脚详细信息)")
        print("6. Display all information (显示所有信息)")
        print("0. Exit (退出)")
        
        try:
            choice = input("\nEnter your choice (输入您的选择): ").strip()
            
            if choice == '0':
                print("Exiting... (退出...)")
                break
            elif choice == '1':
                gpio_info.display_pinout()
            elif choice == '2':
                gpio_info.display_gpio_summary()
            elif choice == '3':
                gpio_info.display_available_gpio()
            elif choice == '4':
                gpio_info.display_power_distribution()
            elif choice == '5':
                pin_input = input("Enter pin numbers (comma-separated, e.g., 1,2,3): ")
                try:
                    pin_numbers = [int(p.strip()) for p in pin_input.split(',')]
                    gpio_info.display_pin_details(pin_numbers)
                except ValueError:
                    print("Invalid input. Please enter numbers separated by commas.")
            elif choice == '6':
                gpio_info.display_pinout()
                gpio_info.display_gpio_summary()
                gpio_info.display_available_gpio()
                gpio_info.display_power_distribution()
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nExiting... (退出...)")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    gpio_info.cleanup()
    print("\nGPIO information query completed. (GPIO信息查询完成)")

if __name__ == '__main__':
    main()