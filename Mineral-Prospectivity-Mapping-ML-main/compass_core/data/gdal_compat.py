"""Compatibilité GDAL — venv ou paquets système Debian/Kali."""

from __future__ import annotations

import sys


def import_gdal():
    """Importe le module ``osgeo.gdal``."""
    try:
        from osgeo import gdal

        return gdal
    except ModuleNotFoundError:
        for candidate in (
            "/usr/lib/python3/dist-packages",
            "/usr/local/lib/python3.13/dist-packages",
        ):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
        from osgeo import gdal

        return gdal


def import_osr():
    """Importe le module ``osgeo.osr``."""
    try:
        from osgeo import osr

        return osr
    except ModuleNotFoundError:
        for candidate in (
            "/usr/lib/python3/dist-packages",
            "/usr/local/lib/python3.13/dist-packages",
        ):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
        from osgeo import osr

        return osr


def import_ogr():
    """Importe le module ``osgeo.ogr``."""
    try:
        from osgeo import ogr

        return ogr
    except ModuleNotFoundError:
        for candidate in (
            "/usr/lib/python3/dist-packages",
            "/usr/local/lib/python3.13/dist-packages",
        ):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
        from osgeo import ogr

        return ogr
