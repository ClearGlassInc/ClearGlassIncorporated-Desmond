#!/usr/bin/env python3
"""
Counter-Drone System Management Platform
Complete system for managing anti-drone detection and defeat systems
Author: Generated for Commercial Use
License: Proprietary
"""

import json
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ================== ENUMS & CONSTANTS ==================

class SystemCategory(Enum):
    """System category based on performance and cost"""
    LOWER_COST = "Lower-Cost System ($50K-$150K)"
    HIGH_PERFORMANCE = "High-Performance System ($150K-$1M)"

class SensorType(Enum):
    """Types of sensors used in the system"""
    EO_CAMERA = "Electro-Optical Camera"
    LWIR_UNCOOLED = "Uncooled Long-Wave Infrared"
    MWIR_COOLED = "Cooled Mid-Wave Infrared"
    RADAR = "Radar Integration"
    ACOUSTIC = "Acoustic Sensor"
    RF_DETECTOR = "Radio Frequency Detector"

class DefeatMethod(Enum):
    """Methods to defeat/neutralize drones"""
    RF_JAMMING = "RF Jamming"
    KINETIC = "Kinetic Intercept"
    DIRECTED_ENERGY = "Directed Energy"
    ELECTRONIC_WARFARE = "Electronic Warfare"
    NET_CAPTURE = "Net Capture"

class ThreatLevel(Enum):
    """Threat assessment levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

# ================== DATA CLASSES ==================

@dataclass
class SystemSpecifications:
    """Technical specifications for counter-drone system"""
    system_id: str
    category: SystemCategory
    sensors: List[SensorType]
    detection_range: int  # in meters
    field_of_view: str  # e.g., "Fixed", "Scanning", "360°"
    defeat_methods: List[DefeatMethod]
    continuous_zoom: bool
    stabilized_gimbal: bool
    price_range: str
    
    # Performance metrics
    false_positive_rate: float  # percentage
    min_detectable_size: float  # in centimeters
    max_tracking_targets: int
    response_time: float  # in seconds
    
    # Environmental capabilities
    day_night_operation: bool
    weather_resistant: bool
    max_wind_speed: int  # km/h
    operating_temp_range: str  # e.g., "-20°C to +50°C"

@dataclass
class DroneDetection:
    """Individual drone detection record"""
    detection_id: str
    timestamp: str
    location: Dict[str, float]  # lat, lon, altitude
    drone_size: str  # "Small", "Medium", "Large"
    speed: float  # km/h
    heading: float  # degrees
    threat_level: ThreatLevel
    confidence: float  # 0-1
    sensor_detected_by: List[SensorType]
    false_positive_probability: float

@dataclass
class DefeatOperation:
    """Record of drone defeat/neutralization operation"""
    operation_id: str
    detection_id: str
    timestamp: str
    method_used: DefeatMethod
    success: bool
    time_to_defeat: float  # seconds
    operator: str
    notes: str

@dataclass
class SystemHealthCheck:
    """System health and status monitoring"""
    check_id: str
    timestamp: str
    system_id: str
    sensors_operational: Dict[str, bool]
    last_calibration: str
    battery_level: float  # percentage
    storage_available: float  # GB
    warnings: List[str]
    errors: List[str]

# ================== MAIN SYSTEM CLASS ==================

class CounterDroneSystem:
    """Main class for managing counter-drone operations"""
    
    def __init__(self, system_spec: SystemSpecifications):
        self.system_spec = system_spec
        self.detections: List[DroneDetection] = []
        self.operations: List[DefeatOperation] = []
        self.health_checks: List[SystemHealthCheck] = []
        self.is_active = False
        
    def activate_system(self) -> bool:
        """Activate the counter-drone system"""
        print(f"Activating {self.system_spec.category.value}...")
        # Perform system checks
        health_check = self._perform_health_check()
        if not health_check.errors:
            self.is_active = True
            print("✓ System activated successfully")
            return True
        else:
            print("✗ System activation failed:")
            for error in health_check.errors:
                print(f"  - {error}")
            return False
    
    def deactivate_system(self):
        """Deactivate the system"""
        self.is_active = False
        print("System deactivated")
    
    def detect_drone(self, detection: DroneDetection) -> bool:
        """Process a drone detection"""
        if not self.is_active:
            print("Error: System is not active")
            return False
        
        # Validate detection against false positive criteria
        if detection.false_positive_probability > 0.7:
            print(f"⚠ High false positive probability ({detection.false_positive_probability:.2%}) - requires manual verification")
        
        self.detections.append(detection)
        print(f"\n🎯 DRONE DETECTED")
        print(f"   ID: {detection.detection_id}")
        print(f"   Threat Level: {detection.threat_level.value}")
        print(f"   Confidence: {detection.confidence:.2%}")
        print(f"   Location: Lat {detection.location['lat']:.6f}, Lon {detection.location['lon']:.6f}")
        print(f"   Altitude: {detection.location['altitude']}m")
        print(f"   Speed: {detection.speed} km/h")
        print(f"   Heading: {detection.heading}°")
        
        # Auto-engage if threat level is CRITICAL
        if detection.threat_level == ThreatLevel.CRITICAL:
            print("\n🚨 CRITICAL THREAT - Auto-engaging...")
            self._auto_engage(detection)
        
        return True
    
    def defeat_drone(self, detection_id: str, method: DefeatMethod, operator: str) -> bool:
        """Initiate drone defeat operation"""
        # Find the detection
        detection = next((d for d in self.detections if d.detection_id == detection_id), None)
        if not detection:
            print(f"Error: Detection {detection_id} not found")
            return False
        
        # Check if method is available in this system
        if method not in self.system_spec.defeat_methods:
            print(f"Error: {method.value} not available in this system")
            print(f"Available methods: {[m.value for m in self.system_spec.defeat_methods]}")
            return False
        
        # Execute defeat operation
        operation = DefeatOperation(
            operation_id=f"OP-{len(self.operations)+1:04d}",
            detection_id=detection_id,
            timestamp=datetime.datetime.now().isoformat(),
            method_used=method,
            success=True,  # Simulated - in real system this would be determined by sensors
            time_to_defeat=self.system_spec.response_time + 2.5,  # Simulated
            operator=operator,
            notes=f"Defeated {detection.drone_size} drone using {method.value}"
        )
        
        self.operations.append(operation)
        print(f"\n✓ DEFEAT OPERATION SUCCESSFUL")
        print(f"   Operation ID: {operation.operation_id}")
        print(f"   Method: {method.value}")
        print(f"   Time to Defeat: {operation.time_to_defeat:.1f}s")
        
        return True
    
    def _auto_engage(self, detection: DroneDetection):
        """Automatically engage critical threats"""
        # Use the most effective method available
        if DefeatMethod.KINETIC in self.system_spec.defeat_methods:
            method = DefeatMethod.KINETIC
        elif DefeatMethod.DIRECTED_ENERGY in self.system_spec.defeat_methods:
            method = DefeatMethod.DIRECTED_ENERGY
        else:
            method = self.system_spec.defeat_methods[0]
        
        self.defeat_drone(detection.detection_id, method, "AUTO-SYSTEM")
    
    def _perform_health_check(self) -> SystemHealthCheck:
        """Perform system health check"""
        import random
        
        sensors_status = {
            sensor.value: random.choice([True, True, True, False])  # 75% operational
            for sensor in self.system_spec.sensors
        }
        
        warnings = []
        errors = []
        
        # Check for sensor failures
        for sensor, status in sensors_status.items():
            if not status:
                errors.append(f"{sensor} not responding")
        
        # Check environmental conditions (simulated)
        if random.random() < 0.1:
            warnings.append("High wind conditions detected")
        
        health_check = SystemHealthCheck(
            check_id=f"HC-{len(self.health_checks)+1:04d}",
            timestamp=datetime.datetime.now().isoformat(),
            system_id=self.system_spec.system_id,
            sensors_operational=sensors_status,
            last_calibration="2025-01-28T10:00:00",
            battery_level=random.uniform(60, 100),
            storage_available=random.uniform(100, 500),
            warnings=warnings,
            errors=errors
        )
        
        self.health_checks.append(health_check)
        return health_check
    
    def generate_report(self) -> str:
        """Generate comprehensive system report"""
        report = f"""
{'='*70}
COUNTER-DRONE SYSTEM REPORT
{'='*70}

System Information:
  System ID: {self.system_spec.system_id}
  Category: {self.system_spec.category.value}
  Status: {'ACTIVE' if self.is_active else 'INACTIVE'}
  Detection Range: {self.system_spec.detection_range}m
  
Sensors:
{chr(10).join(f'  • {sensor.value}' for sensor in self.system_spec.sensors)}

Defeat Methods:
{chr(10).join(f'  • {method.value}' for method in self.system_spec.defeat_methods)}

Performance Metrics:
  False Positive Rate: {self.system_spec.false_positive_rate}%
  Minimum Detectable Size: {self.system_spec.min_detectable_size}cm
  Max Tracking Targets: {self.system_spec.max_tracking_targets}
  Response Time: {self.system_spec.response_time}s

Statistics:
  Total Detections: {len(self.detections)}
  Total Operations: {len(self.operations)}
  Successful Defeats: {sum(1 for op in self.operations if op.success)}
  Success Rate: {(sum(1 for op in self.operations if op.success) / len(self.operations) * 100) if self.operations else 0:.1f}%

Recent Detections:
"""
        for detection in self.detections[-5:]:
            report += f"""
  [{detection.timestamp}]
  ID: {detection.detection_id} | Threat: {detection.threat_level.value}
  Confidence: {detection.confidence:.2%} | False Pos Prob: {detection.false_positive_probability:.2%}
"""
        
        report += f"\n{'='*70}\n"
        return report
    
    def export_data(self, filename: str):
        """Export all system data to JSON file"""
        data = {
            "system_spec": asdict(self.system_spec),
            "detections": [asdict(d) for d in self.detections],
            "operations": [asdict(op) for op in self.operations],
            "health_checks": [asdict(hc) for hc in self.health_checks]
        }
        
        # Convert enums to strings for JSON serialization
        def enum_to_str(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=enum_to_str)
        
        print(f"✓ Data exported to {filename}")

# ================== HELPER FUNCTIONS ==================

def create_lower_cost_system() -> SystemSpecifications:
    """Create a lower-cost system configuration"""
    return SystemSpecifications(
        system_id="CDS-LC-001",
        category=SystemCategory.LOWER_COST,
        sensors=[SensorType.EO_CAMERA, SensorType.LWIR_UNCOOLED, SensorType.RF_DETECTOR],
        detection_range=800,
        field_of_view="Fixed",
        defeat_methods=[DefeatMethod.RF_JAMMING],
        continuous_zoom=False,
        stabilized_gimbal=False,
        price_range="$50,000 - $150,000",
        false_positive_rate=12.5,
        min_detectable_size=15.0,
        max_tracking_targets=5,
        response_time=3.5,
        day_night_operation=True,
        weather_resistant=True,
        max_wind_speed=40,
        operating_temp_range="-10°C to +45°C"
    )

def create_high_performance_system() -> SystemSpecifications:
    """Create a high-performance system configuration"""
    return SystemSpecifications(
        system_id="CDS-HP-001",
        category=SystemCategory.HIGH_PERFORMANCE,
        sensors=[
            SensorType.EO_CAMERA, 
            SensorType.MWIR_COOLED,
            SensorType.RADAR,
            SensorType.ACOUSTIC,
            SensorType.RF_DETECTOR
        ],
        detection_range=3000,
        field_of_view="360° Scanning",
        defeat_methods=[
            DefeatMethod.RF_JAMMING,
            DefeatMethod.KINETIC,
            DefeatMethod.DIRECTED_ENERGY,
            DefeatMethod.ELECTRONIC_WARFARE
        ],
        continuous_zoom=True,
        stabilized_gimbal=True,
        price_range="$150,000 - $1,000,000",
        false_positive_rate=3.2,
        min_detectable_size=5.0,
        max_tracking_targets=50,
        response_time=0.8,
        day_night_operation=True,
        weather_resistant=True,
        max_wind_speed=80,
        operating_temp_range="-30°C to +55°C"
    )

# ================== DEMO FUNCTIONS ==================

def run_demo():
    """Run a demonstration of the system"""
    print("\n" + "="*70)
    print("COUNTER-DRONE SYSTEM DEMONSTRATION")
    print("="*70)
    
    # Create high-performance system
    print("\n📡 Initializing High-Performance Counter-Drone System...")
    system = CounterDroneSystem(create_high_performance_system())
    
    # Activate system
    system.activate_system()
    
    # Simulate drone detections
    print("\n" + "-"*70)
    print("DETECTION PHASE")
    print("-"*70)
    
    # Detection 1: Low threat
    detection1 = DroneDetection(
        detection_id="DET-0001",
        timestamp=datetime.datetime.now().isoformat(),
        location={"lat": 34.0522, "lon": -118.2437, "altitude": 150},
        drone_size="Small",
        speed=25.0,
        heading=45,
        threat_level=ThreatLevel.LOW,
        confidence=0.85,
        sensor_detected_by=[SensorType.EO_CAMERA, SensorType.RADAR],
        false_positive_probability=0.15
    )
    system.detect_drone(detection1)
    
    # Detection 2: High threat
    detection2 = DroneDetection(
        detection_id="DET-0002",
        timestamp=datetime.datetime.now().isoformat(),
        location={"lat": 34.0525, "lon": -118.2440, "altitude": 200},
        drone_size="Medium",
        speed=45.0,
        heading=180,
        threat_level=ThreatLevel.HIGH,
        confidence=0.95,
        sensor_detected_by=[SensorType.MWIR_COOLED, SensorType.RADAR, SensorType.ACOUSTIC],
        false_positive_probability=0.05
    )
    system.detect_drone(detection2)
    
    # Detection 3: Critical threat (auto-engages)
    detection3 = DroneDetection(
        detection_id="DET-0003",
        timestamp=datetime.datetime.now().isoformat(),
        location={"lat": 34.0530, "lon": -118.2445, "altitude": 100},
        drone_size="Large",
        speed=60.0,
        heading=270,
        threat_level=ThreatLevel.CRITICAL,
        confidence=0.98,
        sensor_detected_by=[SensorType.EO_CAMERA, SensorType.MWIR_COOLED, SensorType.RADAR],
        false_positive_probability=0.02
    )
    system.detect_drone(detection3)
    
    # Manual defeat of first detection
    print("\n" + "-"*70)
    print("MANUAL DEFEAT OPERATION")
    print("-"*70)
    system.defeat_drone("DET-0001", DefeatMethod.RF_JAMMING, "OPERATOR-ALPHA")
    
    # Generate report
    print("\n" + "-"*70)
    print("SYSTEM REPORT")
    print("-"*70)
    print(system.generate_report())
    
    # Export data
    system.export_data("counter_drone_system_data.json")
    
    # Deactivate
    print("\n" + "-"*70)
    system.deactivate_system()
    print("="*70)

# ================== MAIN EXECUTION ==================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
    else:
        print("""
Counter-Drone System Management Platform
========================================

Usage:
  python counter_drone_system.py --demo    Run demonstration
  
Features:
  • Multi-sensor integration (EO, LWIR, MWIR, Radar, Acoustic, RF)
  • Real-time drone detection and tracking
  • Multiple defeat methods (RF Jamming, Kinetic, Directed Energy)
  • Threat level assessment with auto-engagement
  • False positive mitigation
  • System health monitoring
  • Comprehensive reporting and data export
  
System Categories:
  • Lower-Cost Systems ($50K-$150K)
  • High-Performance Systems ($150K-$1M)
        """)
        
        # Run demo anyway
        run_demo()
