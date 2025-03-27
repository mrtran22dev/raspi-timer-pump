''' 
this is just a code snippet if using infinite loop for global_timer_count()
replace the global_timer_count() method, btn_callback(), main() sections in main code
'''


##################### global_timer_count() - infinite loop way ######################
async def global_timer_count():
   global timer

   while True:
     while GPIO.input(GPIO_BTN_LED) == GPIO.HIGH:
         print(f"Timer started - timer = {timer}")
         if timer == 0:
             timer = 10
             GPIO.output(GPIO_RELAY, GPIO.HIGH)  		# turn on pump
             await asyncio.sleep(PUMP_TIME)
             print("awaiting pump to finish ... ")
             GPIO.output(GPIO_RELAY, GPIO.LOW)			# turn off pump
         else:
             timer -= 1
             print(f"*********** timer: {timer} *************")
             await asyncio.sleep(1)
     print("Timer stopped")
     GPIO.output(GPIO_RELAY, GPIO.LOW)                   	# turn off pump
     await asyncio.sleep(0.2)



def btn_callback(channel):
    if channel == GPIO_START_STOP:
        ########## used with global_timer_count() infinite loop method ###########
       print('Toggle GPIO_BTN_LED')
       current_state = GPIO.input(GPIO_BTN_LED)
       GPIO.output(GPIO_BTN_LED, not current_state)
       new_state = GPIO.input(GPIO_BTN_LED)
       print(f"current state: {current_state}")
       print(f"new state: {new_state}")


async def main():
   await asyncio.gather(menu_lcd(), led_blink(), global_timer_count())