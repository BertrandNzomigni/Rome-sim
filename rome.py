from random import randint
from random import choice
import logging

logger = logging.getLogger("SIM")
logging.basicConfig(filename='myapp.log',filemode='w', level=logging.INFO)






class Sim:
    def __init__(self):
        self.roman_republic_exist = True
        self.italy_size = 1000
        self.beginning_year = 509
        self.year = self.beginning_year
        self.duration = 50
        self.roman_republic_size = 5
        self.is_at_war = False
        self.war_progression = 0
        self.roman_republic_exist = True
        self.roman_soldiers = 3000
        self.socii_soldiers = 0
        self.wariness_war = False

        self.default_battle_losses = 200

        # Senate

        self.pro_war_influence = 60

        # Diplomacy

        self.is_at_war_with = ["Etruscans"]

        self.country_info = {"Etruscans" : {"army size":3000},"Samnites":{"army size":5000}}


    def incase_defeat(self):
        if self.roman_republic_size <= 0:
            self.log("The roman republic disapears.")
            self.roman_republic_exist = False
    
    def log(self,text):
        logger.info("["+str(self.year)+" BC] " + text)
        
    def run(self):
        while self.year > self.beginning_year - self.duration and self.roman_republic_exist:
            for ennemy in self.is_at_war_with:
                if self.roman_soldiers + self.socii_soldiers > 0: 
                    self.log(f"{self.roman_soldiers} romans soldiers and {self.socii_soldiers} socii soldiers faces {self.country_info[ennemy]["army size"]} soldiers from {ennemy}")
                    ## Battle
                    neighbor_soldier = self.country_info[ennemy]["army size"]

                    roman_morale = 100
                    neighbor_morale = 100

                    cumulative_roman_losses = 0

                    while roman_morale > 0 and neighbor_morale > 0:
                        roman_losses = int(min(neighbor_soldier * 0.01,self.roman_soldiers+self.socii_soldiers))
                        neighbor_losses = int(min((self.roman_soldiers+self.socii_soldiers) * 0.01,neighbor_soldier))

                        cumulative_roman_losses += roman_losses
                        if self.roman_soldiers+self.socii_soldiers > 0: 
                            self.roman_soldiers -= int(roman_losses * self.roman_soldiers/(self.roman_soldiers+self.socii_soldiers))
                        if self.roman_soldiers+self.socii_soldiers > 0:
                            self.socii_soldiers -= int(roman_losses * self.socii_soldiers/(self.roman_soldiers+self.socii_soldiers))
                        neighbor_soldier -= neighbor_losses

                        if roman_losses > neighbor_losses:
                            roman_morale -= 10
                        else:
                            neighbor_morale -= 10

                    self.country_info[ennemy]["army size"] = neighbor_soldier

                    if neighbor_morale <= 0:
                        self.war_progression += 25
                        self.log(f"The roman republic won a battle against {ennemy}. The war advances.")
                        self.log("After this battle, the senatorial pro-war faction gain influence at the expanse of the anti-war faction.")
                        self.pro_war_influence = min(100,self.pro_war_influence + 5)
                        self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                        self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                        if self.war_progression >= 100:
                            self.roman_republic_size += 4
                            self.socii_soldiers += 2000
                            self.is_at_war_with.remove(ennemy)

                            self.log(f"The roman republic won the war against {ennemy}. It annexes partially its territory")
                            self.log("The defeated neighbor will contributes 2000 soldiers to future campaigns.")
                            self.log(f"The socii contributes up to {self.socii_soldiers} soldiers.")
                            self.log(f"Size of the roman republic {self.roman_republic_size}.")

                            self.log("The senatorial pro-war faction ideas are applauded after this victory.")
                            self.pro_war_influence = min(100,self.pro_war_influence + 10)
                            self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                            
                    else:
                        self.war_progression -= 25
                        self.log(f"The roman republic lost a battle against {ennemy}. The war stalls.")
                        self.log("After this battle, the senatorial anti-war faction gain influence at the expanse of the pro-war faction.")
                        self.pro_war_influence = min(100,self.pro_war_influence - 5)
                        self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                        self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                        if self.war_progression <= -100:
                            self.roman_republic_size = max(self.roman_republic_size-4,0)
                            self.is_at_war_with.remove(ennemy)

                            self.log(f"The roman republic lost the war against {ennemy}. It loses some of its territory.")
                            
                            self.log("Size of the roman republic : "+str(self.roman_republic_size)+".")
                            self.incase_defeat()

                            self.log("The senatorial anti-war faction ideas are more considered after this costly defeat.")
                            self.pro_war_influence = max(min(100,self.pro_war_influence - 20),0)
                            self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                if self.roman_soldiers + self.socii_soldiers == 0:
                    self.log(f"The {ennemy} profits from the devasted roman army and destroy Rome.")
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

            if len(self.is_at_war_with) == 0 and randint(0,100) < 30:
                self.log("The romans become more thirsty for war after this period of peace. The pro-war faction benefits.")
                self.pro_war_influence = min(100,self.pro_war_influence + 5)
                self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

            if self.wariness_war and len(self.is_at_war_with) > 0:
                for ennemy in self.is_at_war_with:
                    self.log(f"The senate negotiates a peace with {ennemy}. It accept a peace in exchange of a tribute.")
                    self.is_at_war_with.remove(ennemy)
     
            if randint(0,100) < 30 and len(self.is_at_war_with) == 0 and not self.wariness_war:
                target = None
                while target == None:
                    x = choice(list(self.country_info.keys()))
                    if x not in self.is_at_war_with:
                        target = x
                self.log(f"A consul seek glory. The Roman republic declare war on {target}.")
                self.is_at_war_with.append(target)
                self.war_progression = 0
            
            if randint(0,100) < 30:
                self.log("200 new citizens of Rome are ready for war.")
                self.roman_soldiers += 200
                self.log("The roman republic have "+str(self.roman_soldiers)+" soldiers (without socii).")

            self.year -= 1

s = Sim()
s.run()