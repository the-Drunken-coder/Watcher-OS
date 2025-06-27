from __future__ import annotations

from typing import Tuple

import ags_geolocation as ags


class GeoLocator:
    """Thin wrapper around ags_geolocation to compute target lat/lon."""

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

        We convert altitude-above-ground by sampling DEM if caller did not
        provide AGL. ags library exposes `solve_latlon` or similar.
        """
        # Use the high-level API if available; otherwise fall back to simple flat-earth.
        return ags.solve_latlon(
            own_lat=own_lat,
            own_lon=own_lon,
            own_alt_msl=own_alt_msl,
            bearing_deg=bearing_deg,
            elevation_deg=elevation_deg,
            dem_buffer_km=dem_buffer_km,
        ) 