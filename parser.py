import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Dict, Any


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
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
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

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
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

        profile_data: List[Dict[str, Any]] = []
        last: Dict[str, Any] = {
            "time": 0,
            "depth": 0.0,
            "ndl": 0,
            "tts": 0,
            "temperature": 0.0,
            "pressure": [0.0] * len(cylinders),
            "stop_depth": 0.0,
            "stop_time": 0,
            "gas": "21/00",  # TODO: derive from actual gas change events
        }

        for s in samples:
            attrs = s.attrib
            time_s = _parse_time_to_seconds(attrs.get("time"))

            if "depth" in attrs:
                last["depth"] = float(attrs["depth"].replace(" m", ""))
            if "ndl" in attrs:
                last["ndl"] = int(attrs["ndl"].replace(" min", "").split(":")[0])
            if "tts" in attrs:
                last["tts"] = int(attrs["tts"].replace(" min", "").split(":")[0])
            if "temp" in attrs:
                last["temperature"] = float(attrs["temp"].replace(" C", ""))
            if "stopdepth" in attrs:
                last["stop_depth"] = float(attrs["stopdepth"].replace(" m", ""))
            if "stoptime" in attrs:
                last["stop_time"] = int(attrs["stoptime"].replace(" min", "").split(":")[0])

            for i in range(len(cylinders)):
                key = f"pressure{i}"
                if key in attrs:
                    try:
                        last["pressure"][i] = float(attrs[key].replace(" bar", ""))
                    except ValueError:
                        continue

            profile_data.append({
                "time": time_s,
                "depth": last["depth"],
                "ndl": last["ndl"],
                "tts": last["tts"],
                "temperature": last["temperature"],
                "pressure": last["pressure"].copy(),
                "gas": last["gas"],
                "stop_depth": last["stop_depth"],
                "stop_time": last["stop_time"],
            })

        print(f"Parsed {len(profile_data)} samples from dive log.")
        # print("Sample data:", profile_data[:3])  # Print first 3 samples for debugging
        return profile_data


# Parser registry
PARSER_REGISTRY = {
    ".ssrf": SubsurfaceParser(),
}


def parse_dive_log(file_path: str) -> List[Dict[str, Any]]:
    for ext, parser in PARSER_REGISTRY.items():
        if file_path.lower().endswith(ext):
            return parser.parse(file_path)
    raise UnsupportedFormatError(file_path)
