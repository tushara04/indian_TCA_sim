updates as of 9th nov: 
1. for the multi-lane, the primary reference is Rickert et al. 1995
2. rickert's paper does the line change step in parallel and has to handle two cars grabbing the same cell. to avoid this, in my version the cars are processed in random order by checking if the target cell is empty at the moment each one moves. (this is added as a last bit in the step function of nashctraffic class) -- also note that irl, this might not actually be random -- so what actually determines it has to be figured and then accordingly implemented.

1. car with different sizes
2. car with different velocities
3. what is the case we are trying to make and what do we need to plot to make that case
4. check what people have said about the indian traffic


---
changes being made as of 23rd nov: 
1. renamed the "Crossing: steps between crossings" to "Crossing: off-road wait"

after "off-road wait" number of steps a pedestrian comes, waits for "steps per lane" number of steps, moves to a different lane, again waits and moves, until the last lane, and once it goes off-road, after off-road wait number of steps, another pedestrian appears. 

2. but i want multiple pedestrians to be allowed -- and at multiple locations -- and whether another pedestrian appears or not should not depend on whether the current pedestrian has already crossed.

for this, removed crossing_x = 30 variable from the NaSchTraffic.__init__
because that defines the where the obstacle appears

after the changes:
- the pedestrians appear at every off-road wait number of steps regardless of whether a pedestrian has crossed the road or not
- where they appear in the x-axis is picked uniformly at random
- a pedestrian waits for steps per lane number of steps and then tries to cross. if there's a vehicle in that cell, then it tries again in the next step.
- the number of active pedestrians depends on the ratio of crossing time to spawn interval:
minimum time to cross = lanes x crossing_dwell (steps per lane)
so average active pedestrians = minimum time to cross / crossing_gap
crossing_gap is the number of steps before another pedestrian spawns.

so e.g. if dwell=6 and gap=5 for 5 lanes then 5*6 = 30 steps to cross the road. and a new one spawns every 5 step. so 30/5 = 6 pedestrians at any given time

3. the way lane changing works is through the following questions:
- am i blocked in my current lane?
v_want = current speed + 1 (<= max speed), if at least v_want empty cells, no switch.
- which adjacent lanes exist?
this to check if a car is in lane 0 or last lane because then only one choice is available, and for those in the middle, random allocation of a lane
- is the target lane open and safe?
three parameters to verify:
    - is the side cell empty?
    - will the new lane allow for v_want without braking?
    - is there at least general_max_speed empty cells behind so a fast-approaching vehicle isn't cut off?
- do i change the lane?
probability:
    - change_prob = 1.0; decisive/aggressive drives, will change if given the chance
    - change_prob = 0.0; dont change even if an obstacle is present
    - 0.0 < change_prob < 1.0; driver hesitation or reaction delay; on average, wait time = 1/change_prob

4. red light
no behavioral change (like speed up if it's close to red light so that they are not stuck, or drive in yellow light)