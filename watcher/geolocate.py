from __future__ import annotations

import math
from typing import Tuple


class GeoLocator:
    """Thin wrapper around geolocation to compute target lat/lon."""

    def __init__(self):
        pass

    def locate_target(
        self,
        own_lat: float,
        own_lon: float,
        own_alt_msl: float,
        bearing_deg: float,
        elevation_deg: float,
        dem_buffer_km: float = 5.0,
    ) -> Tuple[float, float]:
        """Return (lat, lon) of the observed target.

        Simple flat-earth approximation for testing.
        In production, this would use a proper geolocation library.
        """
        # Convert to radians
        bearing_rad = math.radians(bearing_deg)
        elevation_rad = math.radians(elevation_deg)
        
        # Simple flat-earth approximation
        # Assume ground level at 0m elevation and estimate horizontal distance
        if elevation_rad <= 0:
            # Looking down or horizontally - use altitude as height
            horizontal_distance_m = abs(own_alt_msl / math.tan(elevation_rad)) if elevation_rad != 0 else 1000
        else:
            # Looking up - assume target at same altitude for now
            horizontal_distance_m = 1000  # Default distance
        
        # Convert distance to lat/lon offsets (very rough approximation)
        # 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(latitude) meters
        
        lat_offset = (horizontal_distance_m * math.cos(bearing_rad)) / 111000
        lon_offset = (horizontal_distance_m * math.sin(bearing_rad)) / (111000 * math.cos(math.radians(own_lat)))
        
        target_lat = own_lat + lat_offset
        target_lon = own_lon + lon_offset
        
        return target_lat, target_lon 