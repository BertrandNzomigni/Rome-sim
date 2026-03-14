import copy
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

        self.roman_war = {"Etruscans":{"occupied cities balance":0}}

        self.country_info = {"Etruscans" : {"army size":3000},"Samnites":{"army size":5000}}

        # Interface
        self.output_this_year = False


    def incase_defeat(self):
        if self.roman_republic_size <= 0:
            self.log("The roman republic disapears.")
            self.roman_republic_exist = False
    
    def log(self,text):
        logger.info("["+str(self.year)+" BC] " + text)
        self.output_this_year = True
        
    def run(self):
        while self.year > self.beginning_year - self.duration and self.roman_republic_exist:
            
            while randint(0,100) < 75 and self.roman_soldiers + self.socii_soldiers > 0 and len(self.roman_war.keys()) > 0:
                ennemy = choice(list(self.roman_war.keys()))
                self.log(f"{self.roman_soldiers} romans soldiers and {self.socii_soldiers} socii soldiers faces {self.country_info[ennemy]["army size"]} soldiers from {ennemy}")


                i = randint(0,1)
                attacker = ["Rome",ennemy][i]
                defender = ["Rome",ennemy][i-1]
                self.log(f"{attacker} is the attacker.")

                ## Battle
                neighbor_soldier = self.country_info[ennemy]["army size"]

                roman_morale = 100
                neighbor_morale = 100

                cumulative_roman_losses = 0

                ennemy_damage_bonus = 0

                if ennemy == "Samnites" and attacker != "Samnites":
                    ennemy_damage_bonus += 25
                    self.log(f"The Samnites are proficient at combat in the hills. They exploit this defensive advantage. (25% damage bonus)")

                while roman_morale > 0 and neighbor_morale > 0:
                    roman_losses = int(min(neighbor_soldier * 0.01 * (1 + ennemy_damage_bonus/100),self.roman_soldiers+self.socii_soldiers))
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

                    if attacker == "Rome":
                        self.log(f"Rome besieges a city of {defender}.")
                        if randint(0,100) < 10:
                            self.log(f"The siege is succesful.")
                            self.roman_war[ennemy]["occupied cities balance"] += 1
                            self.log(f"The balance of occupied cities is {self.roman_war[ennemy]["occupied cities balance"]} in favor of Rome.")
                        else:
                            self.log(f"The siege is unsuccesful.")

                    self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                    if self.war_progression >= 100:
                        annexation_size = max(0,self.roman_war[ennemy]['occupied cities balance'])

                        self.roman_republic_size += annexation_size
                        self.socii_soldiers += 2000
        
                        self.roman_war.pop(ennemy)

                        self.log(f"The roman republic won the war against {ennemy}. It annexes {annexation_size} occupied territories.")
                        self.log("The defeated neighbor will contributes 2000 soldiers to future campaigns.")
                        self.log(f"The socii contributes up to {self.socii_soldiers} soldiers.")
                        self.log(f"Size of the roman republic {self.roman_republic_size}.")

                        self.log("The senatorial pro-war faction ideas are applauded after this victory.")
                        self.pro_war_influence = min(100,self.pro_war_influence + 10)
                        self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                    if self.country_info[ennemy]["army size"] == 0:
                        self.log(f"{ennemy} was destroyed by Rome.")
                        self.country_info.pop(ennemy)
                        if ennemy in self.roman_war.keys():
                            self.roman_war.pop(ennemy)

                        
                else:
                    self.war_progression -= 25
                    self.log(f"The roman republic lost a battle against {ennemy}. The war stalls.")
                    self.log("After this battle, the senatorial anti-war faction gain influence at the expanse of the pro-war faction.")
                    self.pro_war_influence = min(100,self.pro_war_influence - 5)
                    self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

                    self.log("The roman army lost "+str(cumulative_roman_losses)+" soldiers in this battle.")

                    if attacker == ennemy:
                        self.log(f"{ennemy} besieges a city of Rome.")
                        if randint(0,100) < 10:
                            self.log(f"The siege is succesful.")
                            self.roman_war[ennemy]["occupied cities balance"] -= 1
                            self.log(f"The balance of occupied cities is {self.roman_war[ennemy]["occupied cities balance"]} in favor of Rome.")
                        else:
                            self.log(f"The siege is unsuccesful.")

                    if self.war_progression <= -100:
                        
                        annexation_size = max(0,self.roman_war[ennemy]['occupied cities balance'] * -1)

                        self.roman_republic_size = max(self.roman_republic_size-annexation_size,0)

                        self.roman_war.pop(ennemy)

                        self.log(f"The roman republic lost the war against {ennemy}. It loses {annexation_size} territories.")
                        
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

            if len(self.roman_war) == 0 and randint(0,100) < 30:
                self.log("The romans become more thirsty for war after this period of peace. The pro-war faction benefits.")
                self.pro_war_influence = min(100,self.pro_war_influence + 5)
                self.log("The pro-war faction have an influence of "+str(self.pro_war_influence)+"%.")

            if self.wariness_war and len(self.roman_war) > 0:
                current_ennemies = copy.deepcopy(self.roman_war.keys())
                for ennemy in current_ennemies:
                    self.log(f"The senate negotiates a peace with {ennemy}. It accept a peace in exchange of a tribute.")
                    self.roman_war.pop(ennemy)
     
            if randint(0,100) < 30 and len(self.roman_war) == 0 and not self.wariness_war and len(self.country_info) > len(self.roman_war):
                ennemies = self.roman_war.keys()
                target = None
                while target == None:
                    x = choice(list(self.country_info.keys()))                    
                    if x not in ennemies:
                        target = x
                self.log(f"A consul seek glory. The Roman republic declare war on {target}.")
                self.roman_war[target] = {"occupied cities balance":0}
                self.war_progression = 0
            
            if randint(0,100) < 30:
                self.log("200 new citizens of Rome are ready for war.")
                self.roman_soldiers += 200
                self.log("The roman republic have "+str(self.roman_soldiers)+" soldiers (without socii).")

            for country in self.country_info.keys():
                if randint(0,100) < 30:
                    self.log(f"200 new soldiers joins the army of {country}.")
                    self.country_info[country]["army size"] += 200
                    self.log(f"{country} have {self.country_info[country]["army size"]} soldiers.")


            if self.output_this_year:
                logger.info("_________________________")
                self.output_this_year = False
            self.year -= 1

s = Sim()
s.run()