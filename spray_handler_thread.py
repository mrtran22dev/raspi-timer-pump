''' 
this is just a code snippet if using threading instead of asyncio event loop for spray_handler() 
replace the spray_handler() method and btn_callback() sections in main code
'''

################################## spray_handler via threading  #######################################
import threading
spray_thread = None  # Track the spray thread
spray_running = False  # Track if spray is active
last_spray_time = 0  # Track the last spray activation time

def spray_handler():
   global spray_running, spray_thread, last_spray_time
   print("Spray handler started")
   spray_running = True
#    last_spray_time = current_time
   try:
       while GPIO.input(GPIO_SPRAY_BTN) == GPIO.HIGH:
           GPIO.output(GPIO_RELAY, GPIO.HIGH)
           time.sleep(0.01)  				    # Small sleep to avoid blocking
       time.sleep(0.1)  				        # Debounce
       GPIO.output(GPIO_RELAY, GPIO.LOW)
   finally:
       spray_running = False
       spray_thread = None
       print("Spray handler stopped")			# thread automatically terminates when it reaches end of task 
########################################################################################################

def btn_callback(channel):
    print(f"channel = {channel}")
    lcd = lcd_sender.LcdDisplay()
    global menu_page, timer, timer_running, spray_running, spray_thread

    ################## GPIO_SPRAY_BTN via threading ######################
    if channel == GPIO_SPRAY_BTN and not spray_running:
        spray_running = True
        spray_thread = threading.Thread(target=spray_handler, daemon=True)
        spray_thread.start()
        print("Started spray thread")
    