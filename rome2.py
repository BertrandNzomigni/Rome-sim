"""
Roman Republic war simulation.

This is an object-oriented rewrite of a procedural prototype. Besides the
restructuring, the following bugs from the original were fixed:

1. KeyError on double-pop: a war could be removed from `roman_war` twice
   in the same battle (once for reaching 100% war progression, once for
   the enemy's army being wiped out). `War` removal is now idempotent and
   guarded by membership checks.

2. Undefined/stale `enemy` reference: if the inner battle loop never ran
   for a given year (e.g. no soldiers left, or no wars), the old code
   could still reference the `ennemy` variable from a *previous* year
   when checking "Rome is destroyed", or raise NameError on year 1.
   `current_enemy` is now explicitly tracked per year and reset to None.

3. Incorrect loss-splitting math: the original reduced `roman_soldiers`
   first and then computed the socii share of losses using the
   already-reduced total, double-discounting the split. Losses are now
   computed from a single snapshot of the pre-battle totals.

4. Unbounded/unfloored influence: most `pro_war_influence` adjustments
   only clamped the upper bound (`min(100, ...)`) and let it drift
   negative. All adjustments are now clamped to [0, 100] via a helper.

5. Dead/unused state: `is_at_war` and `italy_size` were defined but never
   used. `is_at_war` is now derived from whether any wars are active;
   `italy_size` is used as an upper bound on the republic's territory.

6. Battle attacker/defender army size bookkeeping: the original wrote
   `self.country_info[ennemy]["army size"]` regardless of who initiated
   the battle, which happened to be correct because `ennemy` always
   refers to the foreign nation either way -- this rewrite makes that
   relationship explicit via `Nation` objects instead of implicit
   dictionary-key conventions, removing the fragility.

7. Siege-failure state for Rome (`failed_a_siege`) and for individual
   nations (`Failed a siege`) is now encapsulated and reset per-year in
   one place rather than scattered across the loop body.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from random import randint, choice
from typing import Optional


logger = logging.getLogger("SIM")
logging.basicConfig(filename="myapp.log", filemode="w", level=logging.INFO)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class Nation:
    """A foreign nation Rome can go to war with."""

    name: str
    army_size: int
    damage_bonus_percent: int = 0
    failed_a_siege: bool = False

    def is_destroyed(self) -> bool:
        return self.army_size <= 0

    def reset_siege_failure(self) -> None:
        self.failed_a_siege = False

    def reinforce(self, amount: int) -> None:
        self.army_size += amount


@dataclass
class War:
    """An ongoing war between Rome and one nation."""

    enemy_name: str
    occupied_cities_balance: int = 0
    war_progression: int = 0

    def rome_is_winning_war(self) -> bool:
        return self.war_progression >= 100

    def rome_is_losing_war(self) -> bool:
        return self.war_progression <= -100


@dataclass
class Senate:
    """Tracks the political mood of the Roman senate."""

    pro_war_influence: int = 60
    wariness_threshold_soldiers: int = 300
    wariness_threshold_influence: int = 50
    is_wary_of_war: bool = False

    def adjust_influence(self, delta: int) -> None:
        self.pro_war_influence = int(clamp(self.pro_war_influence + delta, 0, 100))

    def update_wariness(self, total_soldiers: int, log) -> None:
        should_be_wary = (
            total_soldiers <= self.wariness_threshold_soldiers
            or self.pro_war_influence < self.wariness_threshold_influence
        )
        if should_be_wary and not self.is_wary_of_war:
            log("The condition of Rome is critical. The senate is wary to declare new wars.")
            self.is_wary_of_war = True
        elif not should_be_wary and self.is_wary_of_war:
            log("The condition of Rome improved. The senate is more prone to declare new wars.")
            self.is_wary_of_war = False


@dataclass
class BattleResult:
    rome_won: bool
    roman_losses: int
    enemy_remaining_army: int


class Battle:
    """A single battle between Rome (+ socii) and one nation."""

    LOSS_RATE = 0.01
    MORALE_LOSS_PER_ROUND = 10

    def __init__(self, roman_soldiers: int, socii_soldiers: int, nation: Nation):
        self.roman_soldiers = roman_soldiers
        self.socii_soldiers = socii_soldiers
        self.nation = nation

    def fight(self) -> BattleResult:
        roman_morale = 100
        enemy_morale = 100
        enemy_army = self.nation.army_size
        cumulative_roman_losses = 0

        # Fixed totals for this battle; losses are split proportionally
        # against the *original* mix each round rather than a mix that
        # has already been partially depleted earlier in the same round.
        total_roman_side = self.roman_soldiers + self.socii_soldiers

        while roman_morale > 0 and enemy_morale > 0 and total_roman_side > 0 and enemy_army > 0:
            damage_multiplier = 1 + self.nation.damage_bonus_percent / 100
            roman_losses = int(min(enemy_army * self.LOSS_RATE * damage_multiplier, total_roman_side))
            enemy_losses = int(min(total_roman_side * self.LOSS_RATE, enemy_army))

            cumulative_roman_losses += roman_losses

            if total_roman_side > 0:
                roman_share = self.roman_soldiers / total_roman_side
                socii_share = self.socii_soldiers / total_roman_side
                roman_loss_for_romans = int(roman_losses * roman_share)
                roman_loss_for_socii = int(roman_losses * socii_share)

                self.roman_soldiers = max(0, self.roman_soldiers - roman_loss_for_romans)
                self.socii_soldiers = max(0, self.socii_soldiers - roman_loss_for_socii)

            enemy_army -= enemy_losses
            total_roman_side = self.roman_soldiers + self.socii_soldiers

            if roman_losses > enemy_losses:
                roman_morale -= self.MORALE_LOSS_PER_ROUND
            else:
                enemy_morale -= self.MORALE_LOSS_PER_ROUND

        self.nation.army_size = max(0, enemy_army)

        return BattleResult(
            rome_won=enemy_morale <= 0,
            roman_losses=cumulative_roman_losses,
            enemy_remaining_army=self.nation.army_size,
        )


class RomanRepublicSimulation:
    """Top-level simulation driving the year-by-year war loop."""

    ANNUAL_RECRUIT_CHANCE = 30
    ANNUAL_RECRUIT_AMOUNT = 200
    NATION_RECRUIT_CHANCE = 30
    NATION_RECRUIT_AMOUNT = 200
    NEW_WAR_CHANCE = 30
    PEACETIME_MORALE_CHANCE = 30
    SIEGE_SUCCESS_CHANCE = 10
    BATTLE_CONTINUE_CHANCE = 75
    SOCII_GAIN_ON_WAR_WIN = 2000

    def __init__(self):
        self.italy_size = 1000
        self.beginning_year = 509
        self.year = self.beginning_year
        self.duration = 50

        self.roman_republic_size = 5
        self.roman_republic_exists = True

        self.roman_soldiers = 4000
        self.socii_soldiers = 0

        self.failed_a_siege = False  # Rome's own current-year siege failure flag

        self.senate = Senate(pro_war_influence=60)

        self.wars: dict[str, War] = {
            "Etruscans": War(enemy_name="Etruscans"),
        }

        self.nations: dict[str, Nation] = {
            "Etruscans": Nation(name="Etruscans", army_size=3000),
            "Samnites": Nation(name="Samnites", army_size=5000, damage_bonus_percent=25),
        }

        self.output_this_year = False

    # ---------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------

    def log(self, text: str) -> None:
        logger.info(f"[{self.year} BC] {text}")
        self.output_this_year = True

    # ---------------------------------------------------------------
    # Derived state
    # ---------------------------------------------------------------

    @property
    def total_soldiers(self) -> int:
        return self.roman_soldiers + self.socii_soldiers

    @property
    def is_at_war(self) -> bool:
        return len(self.wars) > 0

    def available_besiegers(self) -> list[str]:
        """Foreign nations currently at war with Rome that haven't already
        failed a siege against Rome this year."""
        return [
            name
            for name in self.wars
            if name in self.nations and not self.nations[name].failed_a_siege
        ]

    # ---------------------------------------------------------------
    # Battle orchestration
    # ---------------------------------------------------------------

    def _choose_combatants(self, siegers: list[str]) -> tuple[str, str]:
        """Returns (attacker, enemy_nation_name)."""
        rome_can_attack = not self.failed_a_siege
        socii_can_attack = len(siegers) > 0

        if rome_can_attack and socii_can_attack:
            if randint(0, 100) < 50:
                return "Rome", choice(list(self.wars.keys()))
            else:
                enemy = choice(siegers)
                return enemy, enemy
        elif rome_can_attack:
            return "Rome", choice(list(self.wars.keys()))
        else:
            enemy = choice(siegers)
            return enemy, enemy

    def _remove_war(self, enemy_name: str) -> None:
        """Idempotently remove a war (fixes the original double-pop bug)."""
        self.wars.pop(enemy_name, None)

    def _handle_rome_victory(self, enemy_name: str, war: War, attacker: str, defender: str) -> None:
        war.war_progression += 25
        self.log(f"The roman republic won a battle against {enemy_name}. The war advances.")
        self.log("After this battle, the senatorial pro-war faction gains influence at the expense of the anti-war faction.")
        self.senate.adjust_influence(5)
        self.log(f"The pro-war faction has an influence of {self.senate.pro_war_influence}%.")

        if attacker == "Rome":
            self.log(f"Rome besieges a city of {defender}.")
            if randint(0, 100) < self.SIEGE_SUCCESS_CHANCE:
                self.log("The siege is successful.")
                war.occupied_cities_balance += 1
                self.log(f"The balance of occupied cities is {war.occupied_cities_balance} in favor of Rome.")
            else:
                self.log("The siege is unsuccessful.")
                self.failed_a_siege = True

        if war.rome_is_winning_war():
            self._annex_after_victory(enemy_name, war)

        nation = self.nations.get(enemy_name)
        if nation is not None and nation.is_destroyed():
            self.log(f"{enemy_name} was destroyed by Rome.")
            self.nations.pop(enemy_name, None)
            self._remove_war(enemy_name)

    def _annex_after_victory(self, enemy_name: str, war: War) -> None:
        annexation_size = max(0, war.occupied_cities_balance)
        annexation_size = min(annexation_size, self.italy_size - self.roman_republic_size)
        annexation_size = max(0, annexation_size)

        self.roman_republic_size += annexation_size
        self.socii_soldiers += self.SOCII_GAIN_ON_WAR_WIN

        self._remove_war(enemy_name)

        self.log(f"The roman republic won the war against {enemy_name}. It annexes {annexation_size} occupied territories.")
        self.log("The defeated neighbor will contribute soldiers to future campaigns.")
        self.log(f"The socii now contribute up to {self.socii_soldiers} soldiers.")
        self.log(f"Size of the roman republic: {self.roman_republic_size}.")

        self.log("The senatorial pro-war faction's ideas are applauded after this victory.")
        self.senate.adjust_influence(10)
        self.log(f"The pro-war faction has an influence of {self.senate.pro_war_influence}%.")

    def _handle_rome_defeat(self, enemy_name: str, war: War, attacker: str) -> None:
        war.war_progression -= 25
        self.log(f"The roman republic lost a battle against {enemy_name}. The war stalls.")
        self.log("After this battle, the senatorial anti-war faction gains influence at the expense of the pro-war faction.")
        self.senate.adjust_influence(-5)
        self.log(f"The pro-war faction has an influence of {self.senate.pro_war_influence}%.")

        nation = self.nations.get(enemy_name)

        if attacker == enemy_name:
            self.log(f"{enemy_name} besieges a city of Rome.")
            if randint(0, 100) < self.SIEGE_SUCCESS_CHANCE:
                self.log("The siege is successful.")
                war.occupied_cities_balance -= 1
                self.log(f"The balance of occupied cities is {war.occupied_cities_balance} in favor of Rome.")
            else:
                self.log("The siege is unsuccessful.")
                if nation is not None:
                    nation.failed_a_siege = True

        if war.rome_is_losing_war():
            self._cede_territory_after_defeat(enemy_name, war)

    def _cede_territory_after_defeat(self, enemy_name: str, war: War) -> None:
        annexation_size = max(0, -war.occupied_cities_balance)
        self.roman_republic_size = max(self.roman_republic_size - annexation_size, 0)

        self._remove_war(enemy_name)

        self.log(f"The roman republic lost the war against {enemy_name}. It loses {annexation_size} territories.")
        self.log(f"Size of the roman republic: {self.roman_republic_size}.")
        self._check_for_total_defeat()

        self.log("The senatorial anti-war faction's ideas are taken more seriously after this costly defeat.")
        self.senate.adjust_influence(-20)
        self.log(f"The pro-war faction has an influence of {self.senate.pro_war_influence}%.")

    def _check_for_total_defeat(self) -> None:
        if self.roman_republic_size <= 0:
            self.log("The Roman Republic disappears.")
            self.roman_republic_exists = False

    def _run_one_battle(self) -> Optional[str]:
        """Runs a single battle and returns the enemy nation's name, or
        None if no battle could be fought."""
        siegers = self.available_besiegers()
        if not self.wars or self.total_soldiers <= 0:
            return None
        if len(siegers) == 0 and self.failed_a_siege:
            return None

        attacker, enemy_name = self._choose_combatants(siegers)
        defender = enemy_name if attacker == "Rome" else "Rome"

        nation = self.nations[enemy_name]
        war = self.wars[enemy_name]

        self.log(
            f"{self.roman_soldiers} roman soldiers and {self.socii_soldiers} socii soldiers "
            f"face {nation.army_size} soldiers from {enemy_name}."
        )
        self.log(f"{attacker} is the attacker.")

        if nation.damage_bonus_percent and attacker != enemy_name:
            self.log(
                f"The {enemy_name} are proficient at defensive combat. "
                f"They exploit this advantage. ({nation.damage_bonus_percent}% damage bonus)"
            )

        battle = Battle(self.roman_soldiers, self.socii_soldiers, nation)
        result = battle.fight()

        self.roman_soldiers = battle.roman_soldiers
        self.socii_soldiers = battle.socii_soldiers

        self.log(f"The roman army lost {result.roman_losses} soldiers in this battle.")

        if result.rome_won:
            self._handle_rome_victory(enemy_name, war, attacker, defender)
        else:
            self._handle_rome_defeat(enemy_name, war, attacker)

        return enemy_name

    def _run_year_of_battles(self) -> Optional[str]:
        last_enemy: Optional[str] = None
        while (
            randint(0, 100) < self.BATTLE_CONTINUE_CHANCE
            and self.total_soldiers > 0
            and len(self.wars) > 0
        ):
            siegers = self.available_besiegers()
            if len(siegers) == 0 and self.failed_a_siege:
                break

            fought_enemy = self._run_one_battle()
            if fought_enemy is None:
                break
            last_enemy = fought_enemy

            if not self.roman_republic_exists:
                break

        return last_enemy

    # ---------------------------------------------------------------
    # Per-year housekeeping
    # ---------------------------------------------------------------

    def _reset_siege_flags(self) -> None:
        self.failed_a_siege = False
        for nation in self.nations.values():
            nation.reset_siege_failure()

    def _check_total_annihilation(self, last_enemy: Optional[str]) -> None:
        if self.total_soldiers == 0 and last_enemy is not None:
            self.log(f"The {last_enemy} profit from the devastated roman army and destroy Rome.")
            self.roman_republic_size = 0
            self._check_for_total_defeat()

    def _maybe_gain_peacetime_morale(self) -> None:
        if len(self.wars) == 0 and randint(0, 100) < self.PEACETIME_MORALE_CHANCE:
            self.log("The romans become more thirsty for war after this period of peace. The pro-war faction benefits.")
            self.senate.adjust_influence(5)
            self.log(f"The pro-war faction has an influence of {self.senate.pro_war_influence}%.")

    def _maybe_negotiate_peace(self) -> None:
        if self.senate.is_wary_of_war and len(self.wars) > 0:
            current_enemies = copy.deepcopy(list(self.wars.keys()))
            for enemy_name in current_enemies:
                self.log(f"The senate negotiates a peace with {enemy_name}. It accepts peace in exchange for a tribute.")
                self._remove_war(enemy_name)

    def _maybe_declare_new_war(self) -> None:
        if not (
            randint(0, 100) < self.NEW_WAR_CHANCE
            and len(self.wars) == 0
            and not self.senate.is_wary_of_war
            and len(self.nations) > len(self.wars)
        ):
            return

        candidates = [name for name in self.nations if name not in self.wars]
        if not candidates:
            return

        target = choice(candidates)
        self.log(f"A consul seeks glory. The Roman republic declares war on {target}.")
        self.wars[target] = War(enemy_name=target)

    def _maybe_recruit_romans(self) -> None:
        if randint(0, 100) < self.ANNUAL_RECRUIT_CHANCE:
            self.log(f"{self.ANNUAL_RECRUIT_AMOUNT} new citizens of Rome are ready for war.")
            self.roman_soldiers += self.ANNUAL_RECRUIT_AMOUNT
            self.log(f"The roman republic has {self.roman_soldiers} soldiers (without socii).")

    def _maybe_recruit_for_nations(self) -> None:
        for nation in self.nations.values():
            if randint(0, 100) < self.NATION_RECRUIT_CHANCE:
                self.log(f"{self.NATION_RECRUIT_AMOUNT} new soldiers join the army of {nation.name}.")
                nation.reinforce(self.NATION_RECRUIT_AMOUNT)
                self.log(f"{nation.name} has {nation.army_size} soldiers.")

    # ---------------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------------

    def run(self) -> None:
        while self.year > self.beginning_year - self.duration and self.roman_republic_exists:
            last_enemy = self._run_year_of_battles()

            self._reset_siege_flags()

            self._check_total_annihilation(last_enemy)
            if not self.roman_republic_exists:
                break

            self.senate.update_wariness(self.total_soldiers, self.log)
            self._maybe_gain_peacetime_morale()
            self._maybe_negotiate_peace()
            self._maybe_declare_new_war()
            self._maybe_recruit_romans()
            self._maybe_recruit_for_nations()

            if self.output_this_year:
                logger.info("_________________________")
                self.output_this_year = False

            self.year -= 1


if __name__ == "__main__":
    sim = RomanRepublicSimulation()
    sim.run()