import os
import zipfile
import json
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mafia_fantasy.db')

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_backup():
    """Create a backup of the database and uploads directory"""
    try:
        # Ensure all required directories exist
        for directory in [BACKUP_DIR, UPLOAD_FOLDER, os.path.dirname(DB_FILE)]:
            try:
                os.makedirs(directory, exist_ok=True)
                # Test if directory is writable
                test_file = os.path.join(directory, '.test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Cannot write to directory {directory}: {str(e)}'
                }

        # Create a timestamp for the backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Verify we can write to the backup location
        try:
            with open(backup_path, 'wb') as f:
                f.write(b'test')
            os.remove(backup_path)
        except Exception as e:
            return {
                'success': False,
                'error': f'Cannot write to backup location {backup_path}: {str(e)}'
            }
        
        # Check if we have anything to back up
        if not os.path.exists(DB_FILE) and not os.listdir(UPLOAD_FOLDER):
            return {
                'success': False,
                'error': 'No data to back up - database and uploads directory are empty or not accessible'
            }
        
        # Create a zip file
        zip_created = False
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                if os.path.exists(DB_FILE):
                    zipf.write(DB_FILE, os.path.basename(DB_FILE))
                
                # Add uploads directory
                if os.path.exists(UPLOAD_FOLDER):
                    for root, _, files in os.walk(UPLOAD_FOLDER):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                arcname = os.path.relpath(file_path, os.path.dirname(UPLOAD_FOLDER))
                                zipf.write(file_path, arcname)
                            except Exception as e:
                                # Log error but continue with other files
                                print(f"Error adding {file_path} to backup: {str(e)}")
            
            zip_created = True
            
            # Verify the backup was created
            if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
                return {
                    'success': False,
                    'error': 'Failed to create backup file'
                }
        except Exception as e:
            # Clean up partially created backup file if it exists
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except Exception as cleanup_error:
                    print(f"Error cleaning up backup file: {str(cleanup_error)}")
            
            return {
                'success': False,
                'error': f'Error creating zip file: {str(e)}'
            }
        
        # If we get here, the backup was created successfully
        return {
            'success': True,
            'filename': backup_filename,
            'path': backup_path,
            'size': os.path.getsize(backup_path)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def restore_backup(backup_file):
    """Restore database and uploads from a backup file"""
    try:
        # Create a temporary directory for extraction
        temp_dir = os.path.join(BACKUP_DIR, 'temp_restore')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract the backup
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Restore database
        db_file_in_zip = os.path.join(temp_dir, os.path.basename(DB_FILE))
        if os.path.exists(db_file_in_zip):
            # Create backup of current database
            if os.path.exists(DB_FILE):
                backup_path = f"{DB_FILE}.backup_{int(datetime.now().timestamp())}"
                shutil.copy2(DB_FILE, backup_path)
            
            # Restore database
            shutil.copy2(db_file_in_zip, DB_FILE)
        
        # Restore uploads
        uploads_in_zip = os.path.join(temp_dir, os.path.basename(UPLOAD_FOLDER))
        if os.path.exists(uploads_in_zip):
            # Clear existing uploads
            if os.path.exists(UPLOAD_FOLDER):
                shutil.rmtree(UPLOAD_FOLDER)
            # Copy restored uploads
            shutil.copytree(uploads_in_zip, UPLOAD_FOLDER)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return {
            'success': True,
            'message': 'Database and uploads restored successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Ensure temp directory is removed
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

def get_backup_list():
    """Get a list of available backups"""
    try:
        backups = []
        for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if filename.endswith('.zip') and filename.startswith('backup_'):
                filepath = os.path.join(BACKUP_DIR, filename)
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'created': os.path.getctime(filepath)
                })
        return backups
    except Exception as e:
        print(f"Error getting backup list: {e}")
        return []
