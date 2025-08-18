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
    ppo2: Optional[float] = None  # Partial Pressure of Oxygen in bar
    cns: Optional[int] = None  # Central Nervous System Oxygen Toxicity in %

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
    def __init__(self, message: str = "No dive data found in the dive log file. Please check that the file is a valid dive log."):
        super().__init__(message)


class UnsupportedFormatError(DiveLogError):
    """Raised when the dive log format is not supported."""
    def __init__(self, file_path: str):
        super().__init__(f"Unsupported dive log format for file: {file_path}. Currently supported formats: .ssrf (Subsurface), .xml (Shearwater)")


class DiveParser(ABC):
    """Base class for dive log parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[DiveSample]:
        pass


def _parse_time_to_seconds(t: str | None) -> int:
    if t is None:
        raise NoDiveDataError("Time string cannot be None")
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
            raise NoDiveDataError("No dive computer data found in the dive log. Please check that the dive log contains dive computer information.")

        samples = divecomputer.findall("sample")
        if not samples:
            raise NoDiveDataError("No dive samples found in the dive log. Please check that the dive log contains dive profile data.")

        profile_data: List[DiveSample] = []

        # Initialize last known values
        last_values: DiveSample = DiveSample(
            time=0,
            depth=0.0,
            ndl=99, # Start value for Shearwater
            cns=0, # TODO implement
            ppo2=None, # TODO implement
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

        # Parse gas change events and inject into samples
        events = divecomputer.findall("event")
        gas_changes = []

        for event in events:
            if event.get("name") == "gaschange":
                time_s = _parse_time_to_seconds(event.get("time"))
                o2_str = event.get("o2")
                he_str = event.get("he")

                fraction_o2 = float(o2_str.replace("%", "")) / 100.0 if o2_str else None
                fraction_he = float(he_str.replace("%", "")) / 100.0 if he_str else None

                gas_changes.append({
                    "time": time_s,
                    "fractionO2": fraction_o2,
                    "fractionHe": fraction_he
                })

        gas_changes.sort(key=lambda x: x["time"])

        # Inject gas changes into appropriate samples
        for gas_change in gas_changes:
            target_time = gas_change["time"]

            # Find the first sample at or after the gas change time and inject gas fractions into the target sample and all subsequent samples
            target_sample = None
            for sample in profile_data:
                if sample.time >= target_time:
                    target_sample = sample
                    break

            if target_sample is not None:
                target_index = profile_data.index(target_sample)
                for i in range(target_index, len(profile_data)):
                    profile_data[i].fractionO2 = gas_change["fractionO2"]
                    profile_data[i].fractionHe = gas_change["fractionHe"]

        print(f"Found {len(gas_changes)} gas change events.")
        print(f"Parsed {len(profile_data)} samples from dive log.")
        print("Sample data:", profile_data[:3])  # Print first 3 samples for debugging
        return profile_data


class ShearwaterParser(DiveParser):
    """Parser for Shearwater XML dive logs."""

    def parse(self, file_path: str) -> List[DiveSample]:
        # Handle encoding issues with Shearwater XML files
        try:
            tree = ET.parse(file_path)
        except ET.ParseError:
            # Try reading with UTF-8 and fix encoding declaration
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Replace incorrect encoding declaration
            content = content.replace('encoding="utf-16"', 'encoding="utf-8"')
            tree = ET.fromstring(content)

        root = tree if isinstance(tree, ET.Element) else tree.getroot()

        # Find dive log records
        dive_records = root.findall(".//diveLogRecords/diveLogRecord")
        if not dive_records:
            raise NoDiveDataError("No dive samples found in the dive log. Please check that the dive log contains dive profile data.")

        profile_data: List[DiveSample] = []

        # Initialize last known values
        last_values: DiveSample = DiveSample(
            time=0,
            depth=0.0,
            ndl=99,  # Start value for Shearwater
            pressure=[None] * 4,  # Always 4 tanks in the log
        )

        for record in dive_records:
            time_ms = record.find("currentTime")
            if time_ms is None or time_ms.text is None:
                raise NoDiveDataError("Dive record missing required currentTime field")
            last_values.time = int(time_ms.text) // 1000

            depth_elem = record.find("currentDepth")
            if depth_elem is not None and depth_elem.text is not None:
                last_values.depth = float(depth_elem.text)

            ndl_elem = record.find("currentNdl")
            if ndl_elem is not None and ndl_elem.text is not None and ndl_elem.text.isdigit():
                last_values.ndl = int(ndl_elem.text)

            tts_elem = record.find("ttsMins")
            if tts_elem is not None and tts_elem.text is not None and tts_elem.text.isdigit():
                last_values.tts = int(tts_elem.text)

            temp_elem = record.find("waterTemp")
            if temp_elem is not None and temp_elem.text is not None:
                try:
                    last_values.temperature = float(temp_elem.text)
                except ValueError:
                    pass

            stop_depth_elem = record.find("firstStopDepth")
            if stop_depth_elem is not None and stop_depth_elem.text is not None:
                try:
                    last_values.stop_depth = float(stop_depth_elem.text)
                except ValueError:
                    pass

            stop_time_elem = record.find("firstStopTime")
            if stop_time_elem is not None and stop_time_elem.text is not None:
                try:
                    last_values.stop_time = int(stop_time_elem.text)
                except ValueError:
                    pass

            o2_elem = record.find("fractionO2")
            if o2_elem is not None and o2_elem.text is not None:
                try:
                    last_values.fractionO2 = float(o2_elem.text)
                except ValueError:
                    pass

            he_elem = record.find("fractionHe")
            if he_elem is not None and he_elem.text is not None:
                try:
                    last_values.fractionHe = float(he_elem.text)
                except ValueError:
                    pass

            # tank pressures (convert PSI to bar)
            for i in range(4):
                tank_elem = record.find(f"tank{i}pressurePSI")
                if tank_elem is not None and tank_elem.text is not None:
                    try:
                        psi_value = float(tank_elem.text)
                        last_values.pressure[i] = psi_value * 0.0689476
                    except ValueError:
                        # Handle non-numeric values like "AI is off"
                        last_values.pressure[i] = None

            sac_elem = record.find("sac")
            if sac_elem is not None and sac_elem.text is not None:
                try:
                    last_values.sac = float(sac_elem.text)
                except ValueError:
                    # Handle non-numeric values like "Not diving"
                    pass

            gas_time_elem = record.find("gasTime")
            if gas_time_elem is not None and gas_time_elem.text is not None:
                try:
                    last_values.gtr = int(gas_time_elem.text)
                except ValueError:
                    # Handle non-numeric values like "not available", "due to deco not available"
                    pass

            profile_data.append(copy.deepcopy(last_values))

        print(f"Parsed {len(profile_data)} samples from Shearwater dive log.")
        print("Sample data:", profile_data[:3])  # Print first 3 samples for debugging
        return profile_data


# Parser registry
PARSER_REGISTRY = {
    ".ssrf": SubsurfaceParser(),
    ".xml": ShearwaterParser(),
}


def parse_dive_log(file_path: str) -> List[DiveSample]:
    for ext, parser in PARSER_REGISTRY.items():
        if file_path.lower().endswith(ext):
            return parser.parse(file_path)
    raise UnsupportedFormatError(file_path)
