updates as of 9th nov: 
1. for the multi-lane, the primary reference is Rickert et al. 1995
2. rickert's paper does the line change step in parallel and has to handle two cars grabbing the same cell. to avoid this, in my version the cars are processed in random order by checking if the target cell is empty at the moment each one moves. (this is added as a last bit in the step function of nashctraffic class) -- also note that irl, this might not actually be random -- so what actually determines it has to be figured and then accordingly implemented.

1. car with different sizes
2. car with different velocities
3. what is the case we are trying to make and what do we need to plot to make that case
4. check what people have said about the indian traffic
5. 