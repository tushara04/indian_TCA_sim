'''from mesa import Model, Agent
from mesa.time import SimultaneousActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import numpy as np


class VehicleAgent(Agent):
    """
    Vehicle agent
    """

    def __init__(self, pos, model, max_speed, slow_prob):
        """
        Create a new vehicle agent.
        Args:
           pos: Agent initial position in x, y.
           model: The model the agent is associated with.
           max_speed: The maximum number of cells an agent can move in a single step
        """
        super().__init__(pos, model)
        self.pos = pos
        self.speed = 0
        self.max_speed = max_speed
        self._next_pos = None
        self.slow_prob = slow_prob
        self.space_time = []

    def step(self):
        """
        Calculates the next position of the agent based on several factors:
        - Current Speed
        - Max Speed
        - Proximity of agent ahead of it
        - Random chance of deceleration
        """
        # STEP 1: ACCELERATION
        if self.speed < self.max_speed:
            self.speed += 1

        # STEP 2: DECELERATION
        distance_to_next = 0
        (x, y) = self.pos
        for distance in range(self.max_speed):
            distance += 1
            test_x = x + distance
            test_pos = self.model.grid.torus_adj((test_x, y))
            if self.model.grid.is_cell_empty(test_pos):
                distance_to_next += 1
                if distance_to_next == self.speed:
                    break
            else:
                break
        self.speed = distance_to_next

        # STEP 3: RANDOMISATION
        if self.random.random() < self.slow_prob and self.speed > 0:
            self.speed -= 1

        # STEP 4: MOVEMENT
        self._next_pos = self.pos
        (x, y) = self._next_pos
        x += self.speed
        self._next_pos = self.model.grid.torus_adj((x, y))

        self.model.total_speed = self.model.total_speed + self.speed


    def advance(self):
        """
        Moves the agent to its next position.
        """
        self.model.grid.move_agent(self, self._next_pos)

    def try_change_lane(self):
        m = self.model
        x, y = self.pos
        v_want = min(self.speed + 1, self.max_speed)
    
        # motivation: am I actually blocked?
        if m.gap_ahead(x, y, v_want) >= v_want:
            return
    
        options = [l for l in (y - 1, y + 1) if 0 <= l < m.lanes]
        m.random.shuffle(options)
    
        for y2 in options:
            if not m.grid.is_cell_empty((x, y2)):
                continue                                    # side cell is taken
            if m.gap_ahead(x, y2, v_want) < v_want:
                continue                                    # no improvement there
            if m.gap_behind(x, y2, m.general_max_speed) < m.general_max_speed:
                continue                                    # unsafe for follower
            if self.random.random() < m.change_prob:
                m.grid.move_agent(self, (x, y2))
                m.lane_changes += 1
                return


class NaSchTraffic(Model):
    """
    Model class for the Nagel and Schreckenberg traffic model.
    """

    def __init__(self, height=2, width=60, vehicle_quantity=5, general_max_speed=4, slow_prob=0.3, change_prob=1.0, seed=None):
        

        super().__init__(seed=seed)
        self.height = height
        self.lanes = height
        self.width = width
        self.vehicle_quantity = min(vehicle_quantity, width*height)
        self.change_prob = change_prob
        self.lane_changes = 0
        
        self.general_max_speed = general_max_speed
        self.schedule = SimultaneousActivation(self)
        self.grid = SingleGrid(width, height, torus=True)
        self.slow_prob = slow_prob

        self.average_speed = 0.0
        self.averages = []
        self.space_time = []
        self.total_speed = 0

        self.datacollector = DataCollector(
            model_reporters={"Average_Speed": "average_speed", "Lane_Changes": "lane_changes",},  # Model-level count of average speed of all agents
            # For testing purposes, agent's individual x position and speed
            agent_reporters={
                "PosX": lambda x: x.pos[0],
                "Speed": lambda x: x.speed,
            },
        )

        # Set up agents
        # We use a grid iterator that returns
        # the coordinates of a cell as well as
        # its contents. (coord_iter)
        cells = list(self.grid.coord_iter())
        self.random.shuffle(cells)
        for vehicle_iter in range(0, self.vehicle_quantity):
            cell = cells[vehicle_iter]
            (content, x, y) = cell
            agent = VehicleAgent((x, y), self, general_max_speed, slow_prob)
            #edited
            #self.grid.position_agent(agent, (x, y))
            self.grid.position_agent(agent, x,y)
            self.schedule.add(agent)

        self.running = True
        self.datacollector.collect(self)

    def gap_ahead(self, x, y, limit):
        gap = 0
        for d in range(1, limit + 1):
            if self.grid.is_cell_empty(self.grid.torus_adj((x + d, y))):
                gap += 1
            else:
                break
        return gap

    def gap_behind(self, x, y, limit):
        gap = 0
        for d in range(1, limit + 1):
            if self.grid.is_cell_empty(self.grid.torus_adj((x - d, y))):
                gap += 1
            else:
                break
        return gap


    def step(self):
        """
        Run one step of the model. Calculate current average speed of all agents.
        """
        if self.schedule.steps == 100:
            self.running = False
        self.total_speed = 0
        # Step all agents, then advance all agents
        self.schedule.step()
        if self.schedule.get_agent_count() > 0:
            self.average_speed = self.total_speed / self.schedule.get_agent_count()
        else:
            self.average_speed = 0
        self.averages.append(self.average_speed)
        # collect data
        self.datacollector.collect(self)

        row = np.zeros(self.width)
        for a in self.schedule.agents:
            row[a.pos[0]] = 1
        self.space_time.append(row)

        self.lane_changes = 0
        if self.lanes > 1:
            cars = list(self.schedule.agents)
            self.random.shuffle(cars)      # random order avoids two cars taking one cell
            for car in cars:
                car.try_change_lane()


'''

import numpy as np
from mesa import Model, Agent
from mesa.time import SimultaneousActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector


class ObstacleAgent(Agent):
    """A blocked cell. It sits on the grid but is never added to the schedule."""

    def __init__(self, uid, model, kind):
        super().__init__(uid, model)
        self.kind = kind            # "fixed" or "crossing"


class VehicleAgent(Agent):
    def __init__(self, pos, model, max_speed, slow_prob):
        super().__init__(pos, model)
        self.pos = pos
        self.speed = 0
        self.max_speed = max_speed
        self.slow_prob = slow_prob
        self._next_pos = None

    def try_change_lane(self):
        m = self.model
        x, y = self.pos
        v_want = min(self.speed + 1, self.max_speed)

        # motivation: am I actually blocked?
        if m.gap_ahead(x, y, v_want) >= v_want:
            return

        options = [l for l in (y - 1, y + 1) if 0 <= l < m.lanes]
        m.random.shuffle(options)

        for y2 in options:
            if not m.grid.is_cell_empty((x, y2)):
                continue
            if m.gap_ahead(x, y2, v_want) < v_want:
                continue
            if m.gap_behind(x, y2, m.general_max_speed) < m.general_max_speed:
                continue
            if self.random.random() < m.change_prob:
                m.grid.move_agent(self, (x, y2))
                m.lane_changes += 1
                return

    def step(self):
        # 1. accelerate
        if self.speed < self.max_speed:
            self.speed += 1

        # 2. brake to avoid whatever is ahead (a car OR an obstacle)
        distance_to_next = 0
        (x, y) = self.pos
        for distance in range(self.max_speed):
            distance += 1
            test_pos = self.model.grid.torus_adj((x + distance, y))
            if self.model.grid.is_cell_empty(test_pos):
                distance_to_next += 1
                if distance_to_next == self.speed:
                    break
            else:
                break
        self.speed = distance_to_next

        # 3. random slowdown
        if self.random.random() < self.slow_prob and self.speed > 0:
            self.speed -= 1

        # 4. compute (but don't yet make) the move
        self._next_pos = self.model.grid.torus_adj((x + self.speed, y))
        self.model.total_speed += self.speed

    def advance(self):
        self.model.grid.move_agent(self, self._next_pos)


class NaSchTraffic(Model):
    def __init__(self, height=2, width=60, vehicle_quantity=5,
                 general_max_speed=4, slow_prob=0.3, change_prob=1.0,
                 obstacle_type="none",
                 obstacle_lane=0, obstacle_x=30, obstacle_length=1,
                 crossing_from="lane 0", crossing_x=30,
                 crossing_dwell=4, crossing_gap=15,
                 seed=None):
        super().__init__(seed=seed)
        self.height = height
        self.lanes = height
        self.width = width
        self.general_max_speed = general_max_speed
        self.slow_prob = slow_prob
        self.change_prob = change_prob
        self.lane_changes = 0
        self.schedule = SimultaneousActivation(self)
        self.grid = SingleGrid(width, height, torus=True)

        self.average_speed = 0.0
        self.averages = []
        self.space_time = []
        self.total_speed = 0

        # obstacles
        self.obstacle_type = obstacle_type
        self.obstacles = []             # fixed obstacle cells
        self.crossing_obs = None        # the moving obstacle
        self.crossing_lane = None       # None = currently off the road
        self.crossing_from = crossing_from
        self.crossing_x = min(crossing_x, width - 1)
        self.crossing_dwell = crossing_dwell
        self.crossing_gap = crossing_gap
        self.crossing_timer = crossing_gap   # steps until the first appearance

        if obstacle_type == "fixed":
            lane = min(obstacle_lane, self.lanes - 1)
            for i in range(min(obstacle_length, width - 1)):
                obs = ObstacleAgent("obstacle_%d" % i, self, "fixed")
                self.grid.place_agent(obs, ((obstacle_x + i) % width, lane))
                self.obstacles.append(obs)
        elif obstacle_type == "crossing":
            self.crossing_obs = ObstacleAgent("crossing", self, "crossing")

        self.datacollector = DataCollector(
            model_reporters={"Average_Speed": "average_speed",
                             "Lane_Changes": "lane_changes"},
            agent_reporters={"PosX": lambda a: a.pos[0],
                             "Speed": lambda a: a.speed},
        )

        # cars go only in cells that are still free
        cells = [(x, y) for x in range(width) for y in range(height)
                 if self.grid.is_cell_empty((x, y))]
        self.vehicle_quantity = min(vehicle_quantity, len(cells))
        self.random.shuffle(cells)
        for i in range(self.vehicle_quantity):
            x, y = cells[i]
            agent = VehicleAgent((x, y), self, general_max_speed, slow_prob)
            self.grid.position_agent(agent, x, y)
            self.schedule.add(agent)

        self.running = True
        self.datacollector.collect(self)

    # helper functions
    def gap_ahead(self, x, y, limit):
        gap = 0
        for d in range(1, limit + 1):
            if self.grid.is_cell_empty(self.grid.torus_adj((x + d, y))):
                gap += 1
            else:
                break
        return gap

    def gap_behind(self, x, y, limit):
        gap = 0
        for d in range(1, limit + 1):
            if self.grid.is_cell_empty(self.grid.torus_adj((x - d, y))):
                gap += 1
            else:
                break
        return gap

    def active_obstacles(self):
        """Obstacles currently on the road (used by the plots)."""
        if self.obstacle_type == "fixed":
            return self.obstacles
        if self.obstacle_type == "crossing" and self.crossing_lane is not None:
            return [self.crossing_obs]
        return []

    def update_crossing(self):
        obs = self.crossing_obs
        cx = self.crossing_x
        start = 0 if self.crossing_from == "lane 0" else self.lanes - 1
        direction = 1 if start == 0 else -1

        self.crossing_timer -= 1

        if self.crossing_lane is None:             # waiting off-road
            if self.crossing_timer <= 0 and self.grid.is_cell_empty((cx, start)):
                self.grid.place_agent(obs, (cx, start))
                self.crossing_lane = start
                self.crossing_timer = self.crossing_dwell
            return

        if self.crossing_timer > 0:                # still dwelling in this lane
            return

        nxt = self.crossing_lane + direction
        if nxt < 0 or nxt >= self.lanes:           # crossed the whole road
            self.grid.remove_agent(obs)
            self.crossing_lane = None
            self.crossing_timer = self.crossing_gap
        elif self.grid.is_cell_empty((cx, nxt)):
            self.grid.move_agent(obs, (cx, nxt))
            self.crossing_lane = nxt
            self.crossing_timer = self.crossing_dwell
        # else: a car is in the next cell, so wait and retry next step

    # one time step
    def step(self):
        if self.schedule.steps == 300:
            self.running = False

        # 0. obstacle moves first so cars react to it this same step
        if self.obstacle_type == "crossing":
            self.update_crossing()

        # 1. lane changes
        self.lane_changes = 0
        if self.lanes > 1:
            cars = list(self.schedule.agents)
            self.random.shuffle(cars)
            for car in cars:
                car.try_change_lane()

        # 2. normal NaSch update
        self.total_speed = 0
        self.schedule.step()
        n = self.schedule.get_agent_count()
        self.average_speed = self.total_speed / n if n > 0 else 0
        self.averages.append(self.average_speed)
        self.datacollector.collect(self)

        # 3. photo of the road: cars = 1, obstacles = 0.5 (grey)
        frame = np.zeros((self.lanes, self.width))
        for a in self.schedule.agents:
            frame[a.pos[1], a.pos[0]] = 1
        for o in self.active_obstacles():
            frame[o.pos[1], o.pos[0]] = 0.5
        self.space_time.append(frame)
