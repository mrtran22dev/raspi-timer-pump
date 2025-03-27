import RPi.GPIO as GPIO
import time
from signal import pause
import asyncio
import lcd_sender


# Global variables
menu_page = None
timer = 10
DEFAULT_TIMER = 10
updated_timer = DEFAULT_TIMER	# init updated_timer to have same time as DEFAULT_TIMER to start
PUMP_TIME = 5
spray_running = False       	# Track if spray is active
event_loop = None           	# Store the event loop globally
timer_running = False       	# Track if timer is running

# Set up GPIO mode (BCM numbering)
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin
GPIO_RELAY = 19
GPIO_BTN1 = 18
GPIO_BTN2 = 23
GPIO_START_STOP = 22
GPIO_MENU_BTN = 17
GPIO_SPRAY_BTN = 27

GPIO_BTN_LED = 24
GPIO_LED2 = 13
GPIO_BLINK = 26
GPIO_SERVO = 12

# Set up the GPIO pin
# OUTPUTS
GPIO.setup(GPIO_RELAY, GPIO.OUT)
GPIO.setup(GPIO_BLINK, GPIO.OUT)
GPIO.setup(GPIO_BTN_LED, GPIO.OUT)
GPIO.setup(GPIO_LED2, GPIO.OUT)
GPIO.setup(GPIO_SERVO, GPIO.OUT)
# init outputs to LOW
GPIO.output(GPIO_RELAY, GPIO.LOW)
GPIO.output(GPIO_BLINK, GPIO.LOW)
GPIO.output(GPIO_BTN_LED, GPIO.LOW)
GPIO.output(GPIO_LED2, GPIO.LOW)
GPIO.output(GPIO_SERVO, GPIO.LOW)

# INPUTS
GPIO.setup(GPIO_BTN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)		    # *** must set/init pull-up/down states. otherwise, leave floating may cause issues
GPIO.setup(GPIO_BTN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_MENU_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_SPRAY_BTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_START_STOP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# Create a PWM instance with 50 Hz frequency (standard for SG90, per datasheet)
pwm = GPIO.PWM(GPIO_SERVO, 50)


async def relay_toggle():
    while True:
        # Set the pin HIGH (3.3V)
        GPIO.output(GPIO_RELAY, GPIO.HIGH)
        print(f"GPIO {GPIO_RELAY} set to HIGH (3.3V)")
        # Hold for 5 seconds (or adjust as needed)
        await asyncio.sleep(3)
        print("Holding HIGH for 3 seconds...")
        GPIO.output(GPIO_RELAY, GPIO.LOW)
        await asyncio.sleep(3)

async def led_blink():
    while True:
      GPIO.output(GPIO_BLINK, GPIO.HIGH)
      await asyncio.sleep(0.5)
      GPIO.output(GPIO_BLINK, GPIO.LOW)
      await asyncio.sleep(0.5)

async def spray_handler():
    global spray_running
    print("Spray handler started")
    try:
        while GPIO.input(GPIO_SPRAY_BTN) == GPIO.HIGH:
            GPIO.output(GPIO_RELAY, GPIO.HIGH)
            await asyncio.sleep(0.01)  # Small sleep to yield control
        await asyncio.sleep(0.5)  # Debounce
        GPIO.output(GPIO_RELAY, GPIO.LOW)
    finally:
        spray_running = False
        print("Spray handler stopped")

async def send_pwm():
    # Start PWM with 0% duty cycle (initially off)
    pwm.start(0)
    # Duty cycle calculation: 2 ms pulse / 20 ms period = 10% duty cycle
    # 2.5% pwm is 180 degree opposite of 12.5% pwm
    while True:
        for duty in [2.5, 5, 7.5, 10, 12.5]:
            print(f"Duty cycle set to {duty}%  GPIO {GPIO_SERVO}")
            pwm.ChangeDutyCycle(duty)
            # Hold the position for 1 seconds
            await asyncio.sleep(2)
    # Stop the servo (optional, set duty cycle to 0)
    pwm.ChangeDutyCycle(0)
#    pwm.stop()

async def menu_lcd():
    global menu_page, updated_timer, DEFAULT_TIMER
    lcd = lcd_sender.LcdDisplay()
    lcd.clear_screen()
    menu_page = lcd.main_menu()
    lcd.send_text(text=f" set timer: {updated_timer}s", row=4)
    lcd.close_serial()

async def global_timer_count():
    global updated_timer, DEFAULT_TIMER # timer, timer_running
    temp_timer = updated_timer

    current_state = GPIO.input(GPIO_BTN_LED)
    GPIO.output(GPIO_BTN_LED, not current_state)	# toggle
    new_state = GPIO.input(GPIO_BTN_LED)
    print(f"current state: {current_state}")
    print(f"new state: {new_state}")

    while GPIO.input(GPIO_BTN_LED) == GPIO.HIGH:
          print(f"Timer started - timer = {temp_timer}")
          if temp_timer == 0:
              print("PUMPING WATER ... ")
              GPIO.output(GPIO_RELAY, GPIO.HIGH)  	# turn on pump
              await asyncio.sleep(PUMP_TIME)
              GPIO.output(GPIO_RELAY, GPIO.LOW)  	# turn off pump
              temp_timer = updated_timer
          else:
              temp_timer -= 1
              print(f"*********** timer: {temp_timer} *************")
              await asyncio.sleep(1)
    print("Timer stopped")
    updated_timer = temp_timer
    GPIO.output(GPIO_RELAY, GPIO.LOW)                   # turn off pump
    GPIO.output(GPIO_BTN_LED, GPIO.LOW)                 # set LED off, or turn on Yellow LED

########################################################################################################

def btn_callback(channel):
    print(f"channel = {channel}")
    lcd = lcd_sender.LcdDisplay()
    global menu_page, updated_timer, DEFAULT_TIMER, spray_running # ,timer_running

    # spray handler
    if channel == GPIO_SPRAY_BTN and not spray_running:
        spray_running = True
        if event_loop:
            # event_loop.create_task(spray_handler())					# designed to be called from SAME thread as event loop. typically requires async context (ie. inside async def method())
            # - OR - 
            asyncio.run_coroutine_threadsafe(spray_handler(), event_loop)		# designed to be called from ANY thread. this is safer/more robust that event_loop.create_task() per grok
        else:
            print("Error: Event loop not available")

    # start/stop program
    if channel == GPIO_START_STOP:
        if event_loop:
            asyncio.run_coroutine_threadsafe(global_timer_count(), event_loop)
        else:
            print("Error: Event loop not available")

    # enters LCD main menu
    elif channel == GPIO_BTN1 and menu_page == 'main':
        lcd.clear_screen()
        menu_page = lcd.change_counter()
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)
    elif channel == GPIO_BTN2 and menu_page == 'main':
        print("GPIO_BTN2 pressed")
        lcd.clear_screen()
        menu_page = lcd.reset_counter()
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)

    # change timer menu - inc/dec timer value
    elif channel == GPIO_BTN1 and menu_page == 'change_counter':
        updated_timer += 5
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)
    elif channel == GPIO_BTN2 and menu_page == 'change_counter':
        if updated_timer > 0:
             updated_timer -= 5
             if updated_timer < 0:
                 updated_timer = 0
        elif updated_timer < 0:
             updated_timer = 0
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)

    # reset menu - reset timer to default (120s) functions
    elif channel == GPIO_BTN1 and menu_page == 'reset':
        updated_timer = DEFAULT_TIMER
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)
    elif channel == GPIO_BTN2 and menu_page == 'reset':
        lcd.send_text(text=f" timer: {updated_timer}s", row=4)

    elif channel == GPIO_MENU_BTN:
        print("GPIO_MENU_BTN pressed")
        menu_page = lcd.main_menu()
        print(f"nav to: {menu_page}")
        lcd.send_text(text=f" set timer: {updated_timer}s", row=4)
    # time.sleep(0.1)                                           		# Debounce delay - dont need, already specified debounce in BOUNCETIME


async def toggle_led_test():
    current_state = GPIO.input(GPIO_LED2)
    # Toggle the LED on button press (active low with PUD_DOWN)
    GPIO.output(GPIO_LED2, not current_state)  # Toggle LED state
    print(f"GPIO_MENU pressed > GPIO_LED2 toggled to {'HIGH' if not current_state else 'LOW'}")

###########################################################################################

async def main():
    # Remove any existing event detection
    global event_loop
    event_loop = asyncio.get_running_loop()  # Set event_loop before GPIO setup

    for pin in [GPIO_BTN1, GPIO_BTN2, GPIO_MENU_BTN, GPIO_SPRAY_BTN, GPIO_START_STOP]:
        if GPIO.event_detected(pin):
            GPIO.remove_event_detect(pin)
    # Add event detection for rising edge (button press)
    # bouncetime=200 prevents multiple triggers from button bounce (200 ms debounce)
    BOUNCETIME = 200
    GPIO.add_event_detect(GPIO_BTN1, GPIO.RISING, callback=btn_callback, bouncetime=BOUNCETIME)
    GPIO.add_event_detect(GPIO_BTN2, GPIO.RISING, callback=btn_callback, bouncetime=BOUNCETIME)
    GPIO.add_event_detect(GPIO_MENU_BTN, GPIO.RISING, callback=btn_callback, bouncetime=BOUNCETIME)
    GPIO.add_event_detect(GPIO_SPRAY_BTN, GPIO.RISING, callback=btn_callback, bouncetime=BOUNCETIME)
    GPIO.add_event_detect(GPIO_START_STOP, GPIO.RISING, callback=btn_callback, bouncetime=BOUNCETIME)

#    task1 = asyncio.create_task(led_blink())
    await asyncio.gather(menu_lcd(), led_blink()) #, global_timer_count()) #, relay_toggle())

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    # Set the pin LOW and clean up
    for pin in [GPIO_RELAY, GPIO_BTN_LED, GPIO_BLINK, GPIO_LED2, GPIO_SERVO]:
        GPIO.output(pin, GPIO.LOW)
    pwm.stop()
    GPIO.cleanup()
    print("GPIO cleanup completed, pin set to LOW")