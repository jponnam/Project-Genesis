"""Domain layer: core models, value objects, and domain events.

This layer contains pure domain concepts with no I/O, no framework
coupling, and no dependency on engine or systems. All other layers
may depend on domain; domain depends on nothing inside Civitas Lab.
"""

from __future__ import annotations
