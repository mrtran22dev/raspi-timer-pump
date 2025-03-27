import serial
import time


class LcdDisplay:
    def __init__(self):
        self.SERIAL_PORT = '/dev/ttyAMA0'
        self.BAUD_RATE = 9600
        self.TIMEOUT = 1
        self.ser = serial.Serial(
            port=self.SERIAL_PORT,
            baudrate=self.BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.TIMEOUT
        )
        print(f"Serial port {self.SERIAL_PORT} opened at {self.BAUD_RATE} baud, 8N1.")
    
    def send_instruction(self, instruction, next_byte):
        # No inversion needed—74LS04 handles it
        self.ser.write(bytes([instruction]))
        time.sleep(0.001)
        self.ser.write(bytes([next_byte]))
        time.sleep(0.001)

    def send_text(self, text, row):
        # row_commands = {0: b'\x80', 1: b'\xC0', 2: b'\x94', 3: b'\xD4'}   # Example row addresses
        row_commands = {1: 0x80, 2: 0xC0, 3: 0x94, 4: 0xD4}                 # Example row addresses
        if row in row_commands:
            self.send_instruction(0xFE, row_commands[row])  # Set cursor to the specified row
            self.ser.write(text.encode('utf-8'))            # Send the text
            self.send_instruction(0xFE, 0x0F)	            # show blinking cursor
        else:
            raise ValueError("Invalid row number")

    def clear_screen(self):
        print("Clearing LCD screen...")
        self.send_instruction(0xFE, 0x01)  # Original bytes, not inverted
        time.sleep(0.01)

    def main_menu(self):
        self.clear_screen()
        self.ser.write(b'MAIN MENU:')
        self.send_instruction(0xFE, 0xC0)	        # send decimal <254><192> - start at first character/column at row 2 per LCD backpack manual
        self.ser.write(b' 1. change timer')
        self.send_instruction(0xFE, 0x94)	        # send decimal <254><148> - start at first character/column at row 3 per LCD backpack manual
        self.ser.write(b' 2. reset timer dflt')
        self.send_instruction(0xFE, 0xD4)               # send decimal <254><212> - start at first character/column at row 3 per LCD backpack manual
#        self.ser.write(timer.encode('utf-8'))
        return "main"

    def change_counter(self):
        self.ser.write(b'change timer:')
        self.send_instruction(0xFE, 0xC0)               # send decimal <254><192> - start at first character/column at row 2 per LCD backpack manual
        self.ser.write(b' 1. INC by 5 sec')
        self.send_instruction(0xFE, 0x94)               # send decimal <254><148> - start at first character/column at row 3 per LCD backpack manual
        self.ser.write(b' 2. DEC by 5 sec')
        self.send_instruction(0xFE, 0xD4)               # send decimal <254><212> - start at first character/column at row 3 per LCD backpack manual
        return "change_counter"

    def reset_counter(self):
        self.ser.write(b'reset timer to 120s')
        self.send_instruction(0xFE, 0xC0)               # send decimal <254><192> - start at first character/column at row 2 per LCD backpack manual
        self.ser.write(b' 1. YES')
        self.send_instruction(0xFE, 0x94)               # send decimal <254><148> - start at first character/column at row 3 per LCD backpack manual
        self.ser.write(b' 2. NO')
        return "reset"

    def get_response(self):
        response = self.ser.read(100)
        if response:
            print(f"Response: {response.hex()}")
    
    def close_serial(self):
        if 'ser' in locals():
            self.ser.close()
            print(f"Serial port closed.")