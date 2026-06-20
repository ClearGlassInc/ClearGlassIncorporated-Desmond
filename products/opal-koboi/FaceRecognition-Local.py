#!/usr/bin/env python3
"""
Local Facial Recognition System - Python Implementation
Offline alternative to Azure Face API

LEGAL REQUIREMENTS:
- User consent required before enrollment
- Secure data storage
- Compliance with privacy laws (GDPR, CCPA, BIPA)
- Only for authorized use cases

Author: Facial Recognition System
Version: 1.0
Requires: face_recognition, opencv-python, pillow
"""

import os
import json
import pickle
import face_recognition
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import argparse
import sys

class FaceRecognitionLocal:
    """Local facial recognition system using face_recognition library"""
    
    def __init__(self, database_path: str = "./face_database_local.pkl"):
        self.database_path = database_path
        self.encodings_db = self._load_database()
        self.consent_log = "./consent_log_local.json"
        self.identification_log = "./identification_log_local.json"
        
    def _load_database(self) -> Dict:
        """Load face encodings database"""
        if os.path.exists(self.database_path):
            with open(self.database_path, 'rb') as f:
                return pickle.load(f)
        return {"encodings": [], "names": [], "metadata": []}
    
    def _save_database(self):
        """Save face encodings database"""
        with open(self.database_path, 'wb') as f:
            pickle.dump(self.encodings_db, f)
    
    def _log_consent(self, person_name: str, purpose: str = "facial recognition enrollment"):
        """Log user consent"""
        consent_record = {
            "person_name": person_name,
            "timestamp": datetime.now().isoformat(),
            "purpose": purpose,
            "consent_given": True
        }
        
        if os.path.exists(self.consent_log):
            with open(self.consent_log, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(consent_record)
        
        with open(self.consent_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def _log_identification(self, person_name: str, confidence: float, image_path: str):
        """Log identification event"""
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "person_name": person_name,
            "confidence": confidence,
            "image_path": image_path
        }
        
        if os.path.exists(self.identification_log):
            with open(self.identification_log, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_record)
        
        with open(self.identification_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def get_user_consent(self, person_name: str) -> bool:
        """Display consent form and get user agreement"""
        print("\n" + "="*50)
        print("CONSENT AGREEMENT")
        print("="*50)
        print(f"Person: {person_name}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nBy proceeding, you consent to:")
        print("  - Storage of your facial biometric data")
        print("  - Use of this data for authorized identification")
        print("  - Secure encrypted storage of your information")
        print("\nYou have the right to:")
        print("  - Withdraw consent at any time")
        print("  - Request deletion of your data")
        print("  - Access your stored information")
        print("="*50 + "\n")
        
        consent = input("Type 'I CONSENT' to agree (or anything else to cancel): ")
        
        if consent == "I CONSENT":
            self._log_consent(person_name)
            print("\n✓ Consent recorded successfully.\n")
            return True
        else:
            print("\n✗ Consent not provided. Operation cancelled.\n")
            return False
    
    def enroll_person(self, image_path: str, person_name: str, require_consent: bool = True) -> bool:
        """
        Enroll a person into the facial recognition database
        
        Args:
            image_path: Path to image file
            person_name: Name of the person
            require_consent: Whether to require consent (default: True)
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n{'='*50}")
        print("PERSON ENROLLMENT")
        print(f"{'='*50}\n")
        
        # Get consent if required
        if require_consent and not self.get_user_consent(person_name):
            return False
        
        # Load and verify image
        if not os.path.exists(image_path):
            print(f"✗ Error: Image file not found: {image_path}")
            return False
        
        print(f"Loading image: {image_path}")
        image = face_recognition.load_image_file(image_path)
        
        # Detect faces
        print("Detecting faces...")
        face_locations = face_recognition.face_locations(image, model="hog")
        
        if len(face_locations) == 0:
            print("✗ Error: No face detected in image")
            return False
        
        if len(face_locations) > 1:
            print(f"⚠ Warning: Multiple faces detected ({len(face_locations)}). Using the first face only.")
        
        # Generate face encoding
        print("Generating face encoding...")
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if len(face_encodings) == 0:
            print("✗ Error: Could not generate face encoding")
            return False
        
        encoding = face_encodings[0]
        
        # Add to database
        self.encodings_db["encodings"].append(encoding)
        self.encodings_db["names"].append(person_name)
        self.encodings_db["metadata"].append({
            "enrollment_date": datetime.now().isoformat(),
            "image_path": image_path,
            "face_location": face_locations[0]
        })
        
        self._save_database()
        
        print("\n✓ Enrollment successful!")
        print(f"  Person: {person_name}")
        print(f"  Faces in database: {len(self.encodings_db['names'])}")
        print(f"{'='*50}\n")
        
        return True
    
    def identify_person(self, image_path: str, tolerance: float = 0.6) -> Optional[Dict]:
        """
        Identify a person from an image
        
        Args:
            image_path: Path to image file
            tolerance: Face comparison tolerance (lower = more strict)
        
        Returns:
            Dict with identification results or None
        """
        print(f"\n{'='*50}")
        print("PERSON IDENTIFICATION")
        print(f"{'='*50}\n")
        
        if len(self.encodings_db["encodings"]) == 0:
            print("✗ Error: No enrolled persons in database")
            return None
        
        # Load image
        if not os.path.exists(image_path):
            print(f"✗ Error: Image file not found: {image_path}")
            return None
        
        print(f"Loading image: {image_path}")
        image = face_recognition.load_image_file(image_path)
        
        # Detect faces
        print("Detecting faces...")
        face_locations = face_recognition.face_locations(image, model="hog")
        
        if len(face_locations) == 0:
            print("✗ Error: No face detected in image")
            return None
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if len(face_encodings) == 0:
            print("✗ Error: Could not generate face encoding")
            return None
        
        # Compare with database
        print("Comparing with database...")
        unknown_encoding = face_encodings[0]
        
        # Calculate distances to all known faces
        face_distances = face_recognition.face_distance(
            self.encodings_db["encodings"],
            unknown_encoding
        )
        
        # Find best match
        best_match_index = np.argmin(face_distances)
        best_distance = face_distances[best_match_index]
        
        if best_distance > tolerance:
            print("\n✗ No matching person found")
            print(f"  Best match distance: {best_distance:.3f} (threshold: {tolerance})")
            return None
        
        # Get person info
        person_name = self.encodings_db["names"][best_match_index]
        confidence = 1 - best_distance  # Convert distance to confidence
        metadata = self.encodings_db["metadata"][best_match_index]
        
        result = {
            "person_name": person_name,
            "confidence": confidence,
            "distance": best_distance,
            "enrollment_date": metadata["enrollment_date"],
            "face_location": face_locations[0]
        }
        
        # Log identification
        self._log_identification(person_name, confidence, image_path)
        
        print("\n✓ Person Identified!")
        print(f"  Name: {person_name}")
        print(f"  Confidence: {confidence*100:.2f}%")
        print(f"  Distance: {best_distance:.3f}")
        print(f"  Enrolled: {metadata['enrollment_date']}")
        print(f"{'='*50}\n")
        
        return result
    
    def authenticate_person(self, image_path: str, expected_name: str, tolerance: float = 0.6) -> bool:
        """
        Authenticate that a person in the image matches expected name
        
        Args:
            image_path: Path to image file
            expected_name: Expected person name
            tolerance: Face comparison tolerance
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        result = self.identify_person(image_path, tolerance)
        
        if result and result["person_name"] == expected_name:
            print("✓ Authentication Successful")
            print(f"  Person: {expected_name}")
            print(f"  Confidence: {result['confidence']*100:.2f}%")
            return True
        else:
            print("✗ Authentication Failed")
            if result:
                print(f"  Expected: {expected_name}")
                print(f"  Detected: {result['person_name']}")
            return False
    
    def organize_photos(self, folder_path: str, tolerance: float = 0.6):
        """
        Organize photos in a folder by person
        
        Args:
            folder_path: Path to folder containing photos
            tolerance: Face comparison tolerance
        """
        print(f"\n{'='*50}")
        print("PHOTO ORGANIZATION")
        print(f"{'='*50}\n")
        
        if not os.path.exists(folder_path):
            print(f"✗ Error: Folder not found: {folder_path}")
            return
        
        # Supported image formats
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        
        # Get all image files
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(folder_path).rglob(f"*{ext}"))
            image_files.extend(Path(folder_path).rglob(f"*{ext.upper()}"))
        
        print(f"Found {len(image_files)} images to process\n")
        
        results = []
        
        for image_file in image_files:
            print(f"Processing: {image_file.name}...", end=" ")
            
            try:
                result = self.identify_person(str(image_file), tolerance)
                
                if result:
                    person_name = result["person_name"]
                    print(f"✓ {person_name}")
                    
                    # Create person folder
                    person_folder = Path(folder_path) / person_name
                    person_folder.mkdir(exist_ok=True)
                    
                    # Copy image
                    import shutil
                    shutil.copy2(image_file, person_folder / image_file.name)
                    
                    results.append({
                        "image": image_file.name,
                        "person": person_name,
                        "confidence": result["confidence"]
                    })
                else:
                    print("✗ Unknown")
                    
                    # Create Unknown folder
                    unknown_folder = Path(folder_path) / "Unknown"
                    unknown_folder.mkdir(exist_ok=True)
                    
                    # Copy image
                    import shutil
                    shutil.copy2(image_file, unknown_folder / image_file.name)
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        # Save results
        results_file = Path(folder_path) / "organization_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*50}")
        print("ORGANIZATION COMPLETE")
        print(f"{'='*50}")
        print(f"  Total images: {len(image_files)}")
        print(f"  Identified: {len(results)}")
        print(f"  Unknown: {len(image_files) - len(results)}")
        print(f"  Results saved: {results_file}")
        print(f"{'='*50}\n")
    
    def list_enrolled_persons(self):
        """List all enrolled persons"""
        print(f"\n{'='*50}")
        print("ENROLLED PERSONS")
        print(f"{'='*50}\n")
        
        if len(self.encodings_db["names"]) == 0:
            print("No persons enrolled yet.")
        else:
            for idx, (name, metadata) in enumerate(zip(
                self.encodings_db["names"],
                self.encodings_db["metadata"]
            ), 1):
                print(f"{idx}. {name}")
                print(f"   Enrolled: {metadata['enrollment_date']}")
                print(f"   Image: {metadata['image_path']}")
                print()
        
        print(f"Total: {len(self.encodings_db['names'])} person(s)")
        print(f"{'='*50}\n")
    
    def delete_person(self, person_name: str) -> bool:
        """
        Delete a person from the database
        
        Args:
            person_name: Name of person to delete
        
        Returns:
            bool: True if successful
        """
        indices_to_remove = [
            i for i, name in enumerate(self.encodings_db["names"])
            if name == person_name
        ]
        
        if not indices_to_remove:
            print(f"✗ Person not found: {person_name}")
            return False
        
        # Remove all entries for this person (in reverse to maintain indices)
        for idx in sorted(indices_to_remove, reverse=True):
            del self.encodings_db["encodings"][idx]
            del self.encodings_db["names"][idx]
            del self.encodings_db["metadata"][idx]
        
        self._save_database()
        
        print(f"✓ Deleted {len(indices_to_remove)} face(s) for {person_name}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Local Facial Recognition System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enroll a person
  python FaceRecognition-Local.py enroll --image john.jpg --name "John Doe"
  
  # Identify person from photo
  python FaceRecognition-Local.py identify --image unknown.jpg
  
  # Authenticate specific person
  python FaceRecognition-Local.py authenticate --image webcam.jpg --name "John Doe"
  
  # Organize photos by person
  python FaceRecognition-Local.py organize --folder ./Photos
  
  # List enrolled persons
  python FaceRecognition-Local.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Enroll command
    enroll_parser = subparsers.add_parser('enroll', help='Enroll a new person')
    enroll_parser.add_argument('--image', required=True, help='Path to image file')
    enroll_parser.add_argument('--name', required=True, help='Person name')
    enroll_parser.add_argument('--no-consent', action='store_true', help='Skip consent (testing only)')
    
    # Identify command
    identify_parser = subparsers.add_parser('identify', help='Identify person from image')
    identify_parser.add_argument('--image', required=True, help='Path to image file')
    identify_parser.add_argument('--tolerance', type=float, default=0.6, help='Recognition tolerance (default: 0.6)')
    
    # Authenticate command
    auth_parser = subparsers.add_parser('authenticate', help='Authenticate specific person')
    auth_parser.add_argument('--image', required=True, help='Path to image file')
    auth_parser.add_argument('--name', required=True, help='Expected person name')
    auth_parser.add_argument('--tolerance', type=float, default=0.6, help='Recognition tolerance')
    
    # Organize command
    organize_parser = subparsers.add_parser('organize', help='Organize photos by person')
    organize_parser.add_argument('--folder', required=True, help='Path to folder with photos')
    organize_parser.add_argument('--tolerance', type=float, default=0.6, help='Recognition tolerance')
    
    # List command
    subparsers.add_parser('list', help='List enrolled persons')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete person from database')
    delete_parser.add_argument('--name', required=True, help='Person name to delete')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize system
    fr = FaceRecognitionLocal()
    
    # Execute command
    if args.command == 'enroll':
        success = fr.enroll_person(
            args.image,
            args.name,
            require_consent=not args.no_consent
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'identify':
        result = fr.identify_person(args.image, args.tolerance)
        sys.exit(0 if result else 1)
    
    elif args.command == 'authenticate':
        success = fr.authenticate_person(args.image, args.name, args.tolerance)
        sys.exit(0 if success else 1)
    
    elif args.command == 'organize':
        fr.organize_photos(args.folder, args.tolerance)
    
    elif args.command == 'list':
        fr.list_enrolled_persons()
    
    elif args.command == 'delete':
        success = fr.delete_person(args.name)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
