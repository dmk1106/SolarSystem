Solar System Outline\
  Center: Sun (fixed at the origin, rotating in place)\
  Orbital rings: Planets\
    Each planet has its own orbital radius and own orbital speed\
    Follow circular path around the sun\
      r cos (theta), r sin (theta)\
    Planets also have their own y-axis rotation\
    Shading (and shadows?)\
  Offset orbital: reflective rocket ship (ray tracing)\
    Rocket ship moves on its own orbit, separate from the planets\
  
  Camera modes:\
    Select between camera locked onto rocket ship (3rd person) \
                   manual camera controls using WASD + Mouse\
    Rocket remains on its predefined trajectory regardless\
      (Camera does NOT affect rocket)\
  
  Every render call:\
    Planets advance in orbit and rotation (spin) and calculates shadows\
    Rocket advances in orbit and calculates ray traced reflections\
