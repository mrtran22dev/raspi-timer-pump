# <u>Raspberry Pi - Timer Controlled Switch/Pump</u>

## <u>Scope</u>:
This simple program is intended to control a water pump via spray/pump water continuously in a looped time interval.  
The program is written in Python and all operations (ie. lcd display, global timer, user button interrupts, leds, etc)  
run asyncronously.  

Pump timer interval is preset to default of every 2 mins, but is adjustable via increase/decrease buttons by user.  
- timer menu is displayed on LCD when python script is loaded  
- increase/decrease buttons adjust timer intervals in increments of +/- 5 seconds  
- manual spray button - if spray button is held, pump will activate until button is released  


## <u>To run program</u>:  
1. After cloning repo, navigate to project path and install dependencies:  
    - pip install -r requirements.txt
2. Run all_in.py 

## <u>Schematic</u>:
\<To be added later\>