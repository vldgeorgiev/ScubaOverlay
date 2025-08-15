import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import copy


@dataclass
class DiveSample:
    """Represents a single dive sample with all dive computer data."""
    time: int  # Time in seconds from dive start
    depth: float  # Depth in meters
    ndl: Optional[int] = None  # No Decompression Limit in minutes
    tts: Optional[int] = None  # Time to Surface in minutes
    stop_depth: Optional[float] = 0  # Decompression stop depth in meters
    stop_time: Optional[int] = 0  # Decompression stop time in minutes
    temperature: Optional[float] = None  # Water temperature in Celsius
    pressure: List[Optional[float]] = field(default_factory=list)  # Tank pressures in bar
    fractionO2: Optional[float] = None  # Fraction of oxygen in the gas mix
    fractionHe: Optional[float] = None  # Fraction of helium in the gas mix
    sac: Optional[float] = None  # Surface Air Consumption rate in liters per minute
    gtr: Optional[int] = None  # Gas Time Remaining in seconds


class DiveLogError(Exception):
    """Base exception for dive log parsing errors."""
    pass


class MultipleDivesError(DiveLogError):
    """Raised when a dive log contains multiple dives but only single dives are supported."""
    def __init__(self, dive_count: int):
        self.dive_count = dive_count
        super().__init__(f"The dive log file contains {dive_count} dives. This application currently supports only single dive files. Please export or extract a single dive from your dive log software.")


class NoDiveDataError(DiveLogError):
    """Raised when no dive data is found in the dive log."""
    def __init__(self):
        super().__init__("No dive data found in the dive log file. Please check that the file is a valid dive log.")


class NoDiveComputerDataError(DiveLogError):
    """Raised when no dive computer data is found."""
    def __init__(self):
        super().__init__("No dive computer data found in the dive log. Please check that the dive log contains dive computer information.")


class NoSamplesError(DiveLogError):
    """Raised when no dive samples are found."""
    def __init__(self):
        super().__init__("No dive samples found in the dive log. Please check that the dive log contains dive profile data.")


class UnsupportedFormatError(DiveLogError):
    """Raised when the dive log format is not supported."""
    def __init__(self, file_path: str):
        super().__init__(f"Unsupported dive log format for file: {file_path}. Currently supported formats: .ssrf (Subsurface)")


class DiveParser(ABC):
    """Base class for dive log parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[DiveSample]:
        pass


def _parse_time_to_seconds(t: str | None) -> int:
    if t is None:
        raise ValueError("Time string cannot be None")
    t = t.replace(" min", "").strip()
    parts = list(map(int, t.split(":")))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


class SubsurfaceParser(DiveParser):
    """Parser for Subsurface (.ssrf) XML dive logs."""

    def parse(self, file_path: str) -> List[DiveSample]:
        tree = ET.parse(file_path)
        root = tree.getroot()

        dives = root.findall(".//dives/dive")
        if not dives:
            raise NoDiveDataError()
        if len(dives) > 1:
            raise MultipleDivesError(len(dives))
        dive = dives[0]

        cylinders = dive.findall("cylinder")

        divecomputer = dive.find("divecomputer")
        if divecomputer is None:
            raise NoDiveComputerDataError()

        samples = divecomputer.findall("sample")
        if not samples:
            raise NoSamplesError()

        profile_data: List[DiveSample] = []

        # Initialize last known values
        last_values: DiveSample = DiveSample(
            time=0,
            depth=0.0,
            ndl=99, # Start value for Shearwater
        )
        # Initialize pressures list length based on cylinders (if any)
        if cylinders:
            last_values.pressure = [None] * len(cylinders)

        for s in samples:
            attrs = s.attrib
            time_s = _parse_time_to_seconds(attrs.get("time"))

            # Update last known values only if present in this sample
            last_values.time = time_s
            if "depth" in attrs:
                last_values.depth = float(attrs["depth"].replace(" m", ""))
            if "ndl" in attrs:
                last_values.ndl = int(attrs["ndl"].replace(" min", "").split(":")[0])
            if "tts" in attrs:
                last_values.tts = int(attrs["tts"].replace(" min", "").split(":")[0])
            if "temp" in attrs:
                last_values.temperature = float(attrs["temp"].replace(" C", ""))
            if "stopdepth" in attrs:
                last_values.stop_depth = float(attrs["stopdepth"].replace(" m", ""))
            if "stoptime" in attrs:
                last_values.stop_time = int(attrs["stoptime"].replace(" min", "").split(":")[0])

            # Update tank pressures
            for i in range(len(cylinders)):
                key = f"pressure{i}"
                if key in attrs:
                    try:
                        last_values.pressure[i] = float(attrs[key].replace(" bar", ""))
                    except ValueError:
                        continue

            # Append a full snapshot of the current state
            profile_data.append(copy.deepcopy(last_values))

        print(f"Parsed {len(profile_data)} samples from dive log.")
        print("Sample data:", profile_data[:3])  # Print first 3 samples for debugging
        return profile_data


# Parser registry
PARSER_REGISTRY = {
    ".ssrf": SubsurfaceParser(),
}


def parse_dive_log(file_path: str) -> List[DiveSample]:
    for ext, parser in PARSER_REGISTRY.items():
        if file_path.lower().endswith(ext):
            return parser.parse(file_path)
    raise UnsupportedFormatError(file_path)
