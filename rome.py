from random import randint
import logging

logger = logging.getLogger("SIM")
logging.basicConfig(filename='myapp.log',filemode='w', level=logging.INFO)






class Sim:
    def __init__(self):
        self.roman_republic_exist = True
        self.italy_size = 1000
        self.beginning_year = 509
        self.year = self.beginning_year
        self.duration = 100
        self.roman_republic_size = 5
        self.is_at_war = False
        self.war_progression = 0
        self.is_at_war_etruscans = True
        self.roman_republic_exist = True
        self.roman_soldiers = 3000
        self.socii_soldiers = 0
        self.wariness_war = False

        self.default_battle_losses = 200

        # Senate

        self.pro_war_influence = 40


    def incase_defeat(self):
        if self.roman_republic_size <= 0:
            self.log("The roman republic disapears.")
            self.roman_republic_exist = False
    
    def log(self,text):
        logger.info("["+str(self.year)+" BC] " + text)
        
    def run(self):
        while self.year > self.beginning_year - self.duration and self.roman_republic_exist:
            if self.italy_size > self.roman_republic_size and self.is_at_war and self.roman_soldiers + self.socii_soldiers > 0:
                
                self.log(str(self.roman_soldiers)+" romans soldiers and "+str(self.socii_soldiers)+" socii soldiers faces 3000 soldiers from a neighbor.")
                ## Battle
                neighbor_soldier = 3000

                roman_morale = 100
                neighbor_morale = 100

                cumulative_roman_losses = 0

                while roman_morale > 0 and neighbor_morale > 0:
                    roman_losses = int(min(neighbor_soldier * 0.01,self.roman_soldiers+self.socii_soldiers))
                    neighbor_losses = (self.roman_soldiers+self.socii_soldiers) * 0.01

                    cumulative_roman_losses += roman_losses

                    self.roman_soldiers -= int(roman_losses * self.roman_soldiers/(self.roman_soldiers+self.socii_soldiers))
                    if self.socii_soldiers > 0:
                        self.socii_soldiers -= int(roman_losses * self.socii_soldiers/(self.roman_soldiers+self.socii_soldiers))
                    neighbor_soldier -= neighbor_losses

                    if roman_losses > neighbor_losses:
                        roman_morale -= 10
                    else:
                        neighbor_morale -= 10

                if neighbor_morale <= 0:
                    self.war_progression += 25
                    self.log("The roman republic won a battle against a neighbor. The war advances.")
                    self.log("After this battle, the senatorial pro-war faction gain influence at the expanse of the anti-war faction.")
                    self.pro_war_influence = min(100,self.pro_war_influence + 5)
                    self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                    self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                    if self.war_progression >= 100:
                        self.roman_republic_size += 4
                        self.socii_soldiers += 2000
                        self.log("The roman republic won the war against its neighbor. It annexes partially its territory")
                        self.log("The defeated neighbor will contributes 2000 soldiers to future campaigns.")
                        self.log("The socii contributes up to "+str(self.socii_soldiers)+" soldiers.")
                        self.is_at_war = False
                        self.log("Size of the roman republic : "+str(self.roman_republic_size)+".")

                        self.log("The senatorial pro-war faction ideas are applauded after this victory.")
                        self.pro_war_influence = min(100,self.pro_war_influence + 10)
                        self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")
                else:
                    self.war_progression -= 25
                    self.log("The roman republic lost a battle against a neighbor. The war stalls.")
                    self.log("After this battle, the senatorial anti-war faction gain influence at the expanse of the pro-war faction.")
                    self.pro_war_influence = min(100,self.pro_war_influence - 5)
                    self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                    self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                    if self.war_progression <= -100:
                        self.roman_republic_size = max(self.roman_republic_size-4,0)
                        self.log("The roman republic lost the war against its neighbor. It loses some of its territory.")
                        self.log("Size of the roman republic : "+str(self.roman_republic_size)+".")
                        self.incase_defeat()

                        self.log("The senatorial anti-war faction ideas are more considered after this costly defeat.")
                        self.pro_war_influence = max(min(100,self.pro_war_influence - 10),0)
                        self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

            if self.is_at_war and self.roman_soldiers + self.socii_soldiers == 0:
                self.log("The neighboring ennemy profits from the devasted roman army and destroy Rome.")
                self.roman_republic_size = 0
                self.incase_defeat()

            if not self.roman_republic_exist:
                break
            
            if self.is_at_war_etruscans:

                self.log(str(self.roman_soldiers)+" romans soldiers and "+str(self.socii_soldiers)+" socii soldiers faces 5000 etruscans soldiers.")
                ## Battle
                prob_victory = (self.roman_soldiers+self.socii_soldiers)/(self.roman_soldiers+self.socii_soldiers + 5000)

                if randint(0,100) < prob_victory * 100:
                    self.log("The roman republic won against the etruscans. It annex 1 unit of territory from the Etruscans.")
                    self.roman_republic_size += 1
                    self.log("Size of the roman republic : "+str(self.roman_republic_size)+".")

                    self.log("After this battle, the senatorial pro-war faction gain influence at the expanse of the anti-war faction.")
                    self.pro_war_influence = min(100,self.pro_war_influence + 5)
                    self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")
                else:
                    self.log("The roman republic lost against the etruscans. It lost 1 unit of territory to the Etruscans.")
                    losses = min(self.default_battle_losses,self.roman_soldiers)
                    self.roman_soldiers -= losses
                    self.log(str(losses)+" romans soldiers died.")
                    self.roman_republic_size = max(self.roman_republic_size-1,0)
                    self.log("Size of the roman republic : "+str(self.roman_republic_size)+".")
                    self.incase_defeat()

                    self.log("After this battle, the senatorial anti-war faction gain influence at the expanse of the pro-war faction.")
                    self.pro_war_influence = max(min(100,self.pro_war_influence - 5),0)
                    self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

            if self.is_at_war_etruscans and self.roman_soldiers + self.socii_soldiers == 0:
                self.log("The etruscans profits from the devasted roman army and destroy Rome.")
                self.roman_republic_size = 0
                self.incase_defeat()
            
            if not self.roman_republic_exist:
                break

            if (self.roman_soldiers + self.socii_soldiers <= 300 or self.pro_war_influence < 50) and not self.wariness_war:
                self.log("The conditions of Rome is critical. The senate is wary to declare new wars.")
                self.wariness_war = True
            elif (self.roman_soldiers + self.socii_soldiers > 300 and self.pro_war_influence >= 50) and self.wariness_war:
                self.log("The conditions of Rome improved. The senate is more prone to declare new wars.")
                self.wariness_war = False

            if not self.is_at_war and not self.is_at_war_etruscans and randint(0,100) < 20:
                self.log("The romans become more thirsty for war after this period of peace. The pro-war faction benefits.")
                self.pro_war_influence = min(100,self.pro_war_influence + 5)
                self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

            if self.wariness_war and self.is_at_war_etruscans:
                self.log("The senate negotiates a peace with the Etruscans. The etruscans accept a peace in exchange of a tribute.")
                self.is_at_war_etruscans = False

            if self.wariness_war and self.is_at_war:
                self.log("The senate negotiates a peace with a neighbor. It accept a peace in exchange of a tribute.")
                self.is_at_war = False
     
            if randint(0,100) < 30 and not self.is_at_war and not self.wariness_war:
                self.log("A consul seek glory. The Roman republic declare war on a neighbor.")
                self.is_at_war = True
                self.war_progression = 0

            if randint(0,100) < 20 and self.is_at_war_etruscans:
                self.log("The roman republic makes a white peace with the etruscans.")
                self.is_at_war_etruscans = False
                self.war_progression = 0
            
            if randint(0,100) < 30:
                self.log("200 new citizens of Rome are ready for war.")
                self.roman_soldiers += 200
                self.log("The roman republic have "+str(self.roman_soldiers)+" soldiers (without socii).")

            self.year -= 1

s = Sim()
s.run()