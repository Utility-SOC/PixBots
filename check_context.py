import sys
import os

sys.path.append(os.getcwd())

from hex_system.energy_packet import ProjectileContext

import hex_system.energy_packet
import inspect
with open("context_source.md", "w") as f:
    f.write(f"Module File: {hex_system.energy_packet.__file__}\n")
    f.write("```python\n")
    f.write(inspect.getsource(ProjectileContext))
    f.write("\n```")

c = ProjectileContext()
with open("context_probe.txt", "w") as f:
    f.write(f"Is Dataclass? {hasattr(ProjectileContext, '__dataclass_fields__')}\n")
    if hasattr(ProjectileContext, '__dataclass_fields__'):
        fields = list(ProjectileContext.__dataclass_fields__.keys())
        f.write(f"Has custom_effects field? {'custom_effects' in fields}\n")
        f.write(f"Has modifiers field? {'modifiers' in fields}\n")
        
    f.write(f"Dir has custom_effects? {'custom_effects' in dir(c)}\n")
