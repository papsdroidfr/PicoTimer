import machine, time, _thread
from machine import Timer, Pin, PWM
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB332
from pimoroni import Button, RGBLED

#Objet buzzer to make sounds
class Buzzer():
    ''' passive buzzer soldered in pin0(+) and pin3(grnd)'''
    def __init__(self):
        self.buz = PWM(Pin(0))
        self.on = False #True: play, False: off
    
    def play(self, frequency=440, v=1000):
        """ play one frequency at volume v (1000=max)
        
        Table des fréquences par note/octave:
             0       1      2      3      4      5      6      7      8      9
        do   32.703  65.406 130.81 261.63 523.25 1046.5 2093.  4186.  8372.  16744.
        do#  34.648  69.296 138.59 277.18 554.37 1108.7 2217.5 4434.9 8869.8 17740.
        ré   36.708  73.416 146.83 293.66 587.33 1174.7 2349.3 4698.6 9397.3 18795.
        ré#  38.891  77.782 155.56 311.13 622.25 1244.5 2489.  4978.  9956.1 19912.
        mi   41.203  82.407 164.81 329.63 659.26 1318.5 2637.  5274.  10548. 21096.
        fa   43.654  87.307 174.61 349.23 698.46 1396.9 2793.8 5587.7 11175. 22351.
        fa#  46.249  92.499 185.   369.99 739.99 1480.  2960.  5919.9 11840. 23680.
        sol  48.999  97.999 196.   392.   783.99 1568.  3136.  6271.9 12544. 25088.
        sol# 51.913  103.83 207.65 415.3  830.61 1661.2 3322.4 6644.9 13290. 26580.
        la   55.     110.   220.   440.   880.   1760.  3520.  7040.  14080. 28160.
        la#  58.27   116.54 233.08 466.16 932.33 1864.7 3729.3 7458.6 14917. 29834.
        si   61.735  123.47 246.94 493.88 987.77 1975.5 3951.1 7902.1 15804. 31609.
        """
        self.buz.duty_u16(v%1001)     # set volume (1000=max)
        self.buz.freq(frequency) # play the frequency
        self.on=True
    
    def off(self):
        ''' sounds off '''
        self.buz.duty_u16(0)     # sound off
        self.on = False

    def play_lam(self):
        ''' Am7 chord '''
        for f in [440, 523, 659, 784]:
            self.play(f)
            time.sleep(0.1)
        self.off()

# Objet compte à rebours
class CptRebours():
    #constructeur, initialise timeleft
    def __init__(self, t=0):
        self.timeleft = t
    # fct callbackappelée par le timer
    def countdown(self, tm):    
        if self.timeleft > 0 :
            self.timeleft -= 1

# Objet picodisplay
class Display():
    def __init__(self, s=0):
        ''' constructor s = countdown in secondes'''
        self.s_left = s
        self.button_a = Button(12)
        self.button_b = Button(13)
        self.button_x = Button(14)
        self.button_y = Button(15)
        self.led = RGBLED(6, 7, 8)
        self.refresh_count =  0    # number of screen refreshes

        self.display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=180, pen_type=PEN_RGB332 )
        self.display.set_backlight(0.5)
        
        self.ledOn = False   # led on/off
        self.start = False   # countdown started ?
        
        #init display
        self.led.set_rgb(0,0,0) #clear RGB
        self.display.set_pen(self.display.create_pen(0, 0, 255))  # blue background
        self.display.clear() # Clear the display buffer
        self.print_background()
        self.set_time(s)
    
    #private method      
    def __print_mn(self, mn):
        ''' print minutes '''
        str_mn = '0'*(mn<10) + str(mn) # convert to string xx
        self.display.text(str_mn, 50, 58, scale=6)
        
    def __print_ss(self, ss):
        ''' print secondes '''
        str_ss = '0'*(ss<10) + str(ss) # convert to string xx
        self.display.text(str_ss, 140, 58, scale=6)
        
    def __print_time(self):
        ''' print full time mm : ss '''
        self.display.set_pen(self.display.create_pen(0, 0, 255))  # Set a blue pen
        self.display.rectangle(0,50,240,60)
        self.display.set_pen(self.display.create_pen(255, 255, 255)) # Set a white pen
        self.display.text(":", 120, 65, scale=5)
        self.__print_mn(self.mn)
        self.__print_ss(self.ss)
        self.display.update()

           
    def __add_s(self,s):
        ''' add s secondes to the countdown '''
        #print('add ', s ,' secondes')
        snew = s + self.s_left
        if snew > 90*60:
            snew=0
        self.set_time(snew)

    #public method
    def print_background(self):
        ''' print permanent background and title '''
        self.display.set_pen(self.display.create_pen(25, 25, 112)) # dark blue
        self.display.rectangle(4,2,232,38) 
        self.display.set_pen(self.display.create_pen(255, 215, 0)) # gold
        self.display.set_font("bitmap8")
        self.display.text("<- Init   Start ->", 10, 10, scale=3) # header text
        self.display.text("https://www.papsdroid.fr", 5, 120, scale=2) # footer text
        self.display.update()

    def set_time(self, ss):
        ''' convert ss into mn:ss and display it'''
        self.s_left = ss
        self.mn = ss // 60
        self.ss = ss % 60
        self.__print_time()
        #print('set time :', self.s_left)
    
    def led_blink(self):
        ''' led blink '''
        if self.ledOn:
            self.led.set_rgb(0,0,0) #led off
        else:
            if self.s_left > 30 :
                self.led.set_rgb(0,50,0) # green ligth
            else:
                self.led.set_rgb(50,0,0) # red ligth
        self.ledOn = not(self.ledOn)
    
    def led_off(self):
        self.led.set_rgb(0,0,0) #led off
        self.ledOn=False
    
    def input_time(self):
        ''' set countdonw timer '''
        #ss = int(input("Compte à rebours en secondes: "))       
        while (display.button_b.read() == False): #ends when x is pressed
            if display.button_x.read():
                display.__add_s(60) # add 1mn when button b is pressed
            if display.button_a.read():
                display.__add_s(1) # add 1s when button y is pressed
            time.sleep(0.05)
        #print('set s_left=', self.s_left)
        return (self.s_left)
        

# Fonction exécutée dans le second thread 
# gère l'affichage sur le picodisplay
def thread_anim():
    while True:
        
        if (display.s_left == 0):
            display.refresh_count = 0 
            display.led_off()
            
        if display.start:
            if (display.s_left > cptr.timeleft):
                #update the display only if mn or ss are changed
                display.set_time(cptr.timeleft)
            #led blink every 5 refresh
            if (display.refresh_count % 5 == 0):
                display.led_blink()       # blink the led every 5 refresh
                if (display.s_left < 30): # if time left is less than 30s
                    if not(buz.on):       # turn on/off the buzzer
                        buz.play(440)     # play A
                    else:
                        buz.off()
                
            display.refresh_count += 1
        
        time.sleep(0.05)
        
        
        #additionnal waiting if time lieft is more than 10s
        if cptr.timeleft > 10 : 
            time.sleep(0.05)

#initialisation des objets
display = Display()
cptr = CptRebours()
buz = Buzzer()

#démarrage du thread d'animation
_thread.start_new_thread(thread_anim, ()) 

#boucle du thread principal
while True:
    
    #phase initialisation du compte à rebours
    print('init compte à rebours')
    buz.play_lam()                # play a bluesy Am7
    display.print_background()    # display nackground and titles
    cptr = CptRebours(display.input_time()) # init countdouwn
    display.set_time(cptr.timeleft)         # display time left
   
    print('Démarrage compte à rebours ...')
    tim = Timer(period=1000, callback=cptr.countdown) #start timer
    display.start = True
    
    #do nothing unless countdonw ends or button Y (init) is pressed
    while (cptr.timeleft>0) and (display.button_y.read()==False) :
        time.sleep(1)
    
    #countdown ends
    display.start = False
    display.set_time(0)
    print("BIP BIP BIP compte à rebours terminé !")
    tim.deinit() #stop and free the timer
    
    #play sound until button Y (init) is pressed
    while (display.button_y.read()==False) :
        buz.play(466) #play Bb
        time.sleep(0.1)
        buz.off()
        time.sleep(0.1)

