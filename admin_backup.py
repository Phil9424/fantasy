import os
import zipfile
import tempfile
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import (
    Blueprint, jsonify, request, current_app,
    send_file, abort, flash, redirect, url_for
)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_FILE = os.path.join(BASE_DIR, 'instance', 'mafia_fantasy.db')

# Create necessary directories if they don't exist
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for backup routes
backup_bp = Blueprint('backup', __name__, url_prefix='/admin')

def create_backup():
    """Create a backup of the database and uploads"""
    try:
        logger.info("Starting backup creation process")
        
        # Check if backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        logger.debug(f"Backup directory: {BACKUP_DIR}")
        
        # Create a timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
        logger.info(f"Creating backup file: {backup_file}")
        
        # Create a zip file
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file if it exists
                if os.path.exists(DB_FILE):
                    logger.debug(f"Adding database file: {DB_FILE}")
                    zipf.write(DB_FILE, os.path.basename(DB_FILE))
                else:
                    logger.warning(f"Database file not found: {DB_FILE}")
                
                # Add uploads directory if it exists
                if os.path.exists(UPLOAD_FOLDER):
                    logger.debug(f"Adding files from upload folder: {UPLOAD_FOLDER}")
                    file_count = 0
                    for root, _, files in os.walk(UPLOAD_FOLDER):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(UPLOAD_FOLDER))
                            zipf.write(file_path, arcname)
                            file_count += 1
                    logger.info(f"Added {file_count} files from upload folder")
                else:
                    logger.warning(f"Upload folder not found: {UPLOAD_FOLDER}")
        except Exception as e:
            logger.error(f"Error creating zip archive: {str(e)}", exc_info=True)
            raise Exception(f"Ошибка при создании архива: {str(e)}")
        
        # Check if the archive was created
        if not os.path.exists(backup_file):
            error_msg = f"Backup file was not created: {backup_file}"
            logger.error(error_msg)
            raise Exception("Не удалось создать файл резервной копии")
        
        # Get the file size
        file_size = os.path.getsize(backup_file)
        logger.info(f"Backup created successfully: {backup_file} ({file_size} bytes)")
        
        # Return the download URL
        backup_url = f"/admin/backup/download/{os.path.basename(backup_file)}"
        
        return {
            'success': True,
            'download_url': backup_url,
            'filename': os.path.basename(backup_file),
            'size': file_size,
            'created_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f"Ошибка при создании резервной копии: {str(e)}"
        }

def restore_backup(backup_path):
    """Restore database and uploads from a backup"""
    try:
        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        # Extract the backup
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the database file in the extracted files
        db_restored = False
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # If this is the database file
                if file.endswith('.db'):
                    # Create backup of current database
                    if os.path.exists(DB_FILE):
                        backup_path = f"{DB_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(DB_FILE, backup_path)
                    
                    # Replace database
                    shutil.copy2(file_path, DB_FILE)
                    db_restored = True
                
                # If this is from the uploads directory
                elif 'uploads' in rel_path.split(os.sep):
                    # Reconstruct the target path
                    parts = rel_path.split(os.sep)
                    uploads_index = parts.index('uploads')
                    target_path = os.path.join(UPLOAD_FOLDER, *parts[uploads_index+1:])
                    
                    # Ensure target directory exists
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(file_path, target_path)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        if not db_restored:
            return {'success': False, 'error': 'No database file found in backup'}
            
        return {'success': True}
        
    except Exception as e:
        current_app.logger.error(f"Restore failed: {str(e)}")
        return {'success': False, 'error': str(e)}
    
    finally:
        # Ensure temp directory is removed
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

def get_backup_list():
    """Get a list of available backups"""
    try:
        backups = []
        for file in os.listdir(BACKUP_DIR):
            if file.endswith('.zip'):
                file_path = os.path.join(BACKUP_DIR, file)
                backups.append({
                    'name': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    except Exception as e:
        current_app.logger.error(f"Error getting backup list: {str(e)}")
        return []

@backup_bp.route('/backup', methods=['POST'])
def backup():
    """Create a backup of the database and uploads"""
    try:
        current_app.logger.info("=== Starting backup process ===")
        
        # Log request details
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        current_app.logger.info(f"Request data: {request.get_data()}")
        current_app.logger.info(f"Request form: {request.form}")
        current_app.logger.info(f"Request JSON: {request.get_json(silent=True)}")
        current_app.logger.info(f"CSRF Token: {request.headers.get('X-CSRFToken')}")
        
        # CSRF protection temporarily disabled for testing
        current_app.logger.warning("CSRF protection is currently disabled for testing")
        
        # Check if user is admin (you should add your own authentication logic)
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Verify required directories
        required_dirs = [
            BACKUP_DIR,
            os.path.dirname(current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    current_app.logger.info(f"Created directory: {directory}")
                except Exception as e:
                    error_msg = f"Failed to create directory {directory}: {str(e)}"
                    current_app.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 500
        
        # Create backup
        current_app.logger.info("Creating backup...")
        result = create_backup()
        
        if result.get('success'):
            current_app.logger.info(f"Backup created successfully: {result.get('path')}")
            # Return the download URL
            return jsonify({
                'success': True,
                'download_url': f"/admin/backup/download/{os.path.basename(result['path'])}",
                'filename': os.path.basename(result['path'])
            })
        else:
            error_msg = result.get('error', 'Unknown error during backup')
            current_app.logger.error(f"Backup failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        error_msg = f"Unexpected error during backup: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred during backup',
            'details': str(e) if current_app.debug else None
        }), 500

@backup_bp.route('/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    """Download a backup file"""
    try:
        logger.info(f"Attempting to download backup file: {filename}")
        
        # Проверяем, что файл существует и находится в папке бэкапов
        file_path = os.path.join(BACKUP_DIR, filename)
        
        # Защита от path traversal атак
        if not os.path.normpath(file_path).startswith(os.path.abspath(BACKUP_DIR)):
            logger.error(f"Security violation: Attempted path traversal with filename: {filename}")
            abort(403, "Доступ запрещен")
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.error(f"Backup file not found: {file_path}")
            abort(404, "Файл резервной копии не найден")
        
        # Получаем информацию о файле
        file_size = os.path.getsize(file_path)
        logger.info(f"Sending backup file: {file_path} ({file_size} bytes)")
        
        # Отправляем файл с поддержкой докачки
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip',
            conditional=True
        )
        
        # Устанавливаем заголовки для кеширования
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading backup {filename}: {str(e)}", exc_info=True)
        abort(500, f"Ошибка при загрузке резервной копии: {str(e)}")

@backup_bp.route('/restore', methods=['POST'])
def restore():
    """Restore database and uploads from a backup"""
    try:
        # Skip CSRF check for file uploads
        if hasattr(request, '_get_current_object') and hasattr(request, 'form'):
            request._get_current_object().form = request.form
        
        # Check if file was uploaded
        if 'file' not in request.files:
            logger.error('No file part in request')
            return jsonify({'success': False, 'error': 'Не выбран файл для восстановления'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.error('No file selected')
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
            
        if not file.filename.endswith('.zip'):
            logger.error(f'Invalid file type: {file.filename}')
            return jsonify({'success': False, 'error': 'Неверный формат файла. Пожалуйста, загрузите файл в формате .zip'}), 400
        
        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = os.path.join(temp_dir, file.filename)
        
        try:
            # Save the uploaded file
            logger.info(f'Saving uploaded file: {file.filename}')
            file.save(temp_zip_path)
            
            # Extract the backup
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                # Check if the zip contains the database file
                db_file = None
                for name in zip_ref.namelist():
                    if name.endswith('.db'):
                        db_file = name
                        break
                
                if not db_file:
                    error_msg = 'Backup does not contain a database file'
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f'Found database file in backup: {db_file}')
                
                # Extract all files
                logger.info('Extracting backup files...')
                zip_ref.extractall(temp_dir)
            
            # Get the database file path
            extracted_db = os.path.join(temp_dir, db_file)
            
            # Verify the database file exists
            if not os.path.exists(extracted_db):
                error_msg = f'Failed to extract database file from backup: {extracted_db}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Create a backup of the current database if it exists
            if os.path.exists(DB_FILE):
                backup_path = os.path.join(BACKUP_DIR, f'pre_restore_{int(time.time())}.db')
                logger.info(f'Creating backup of current database at: {backup_path}')
                shutil.copy2(DB_FILE, backup_path)
            
            # Replace the current database
            logger.info(f'Restoring database from backup: {extracted_db} -> {DB_FILE}')
            shutil.copy2(extracted_db, DB_FILE)
            
            # Set proper permissions
            os.chmod(DB_FILE, 0o644)
            logger.info('Database permissions updated')
            
            logger.info(f'Successfully restored database from backup: {file.filename}')
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f'Error during restore: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Ошибка при восстановлении из резервной копии: {str(e)}'
            }), 500
            
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(temp_zip_path):
                    logger.debug(f'Removing temporary file: {temp_zip_path}')
                    os.remove(temp_zip_path)
                if os.path.exists(temp_dir):
                    logger.debug(f'Removing temporary directory: {temp_dir}')
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f'Error cleaning up temporary files: {str(e)}', exc_info=True)
        
    except Exception as e:
        logger.error(f"Unexpected error in restore endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500
@backup_bp.route('/download_db')
def download_db():
    """Скачать копию базы данных"""
    try:
        # Проверяем существование файла
        if not os.path.exists(DB_FILE):
            logger.warning(f"Database file not found at {DB_FILE}, creating new database")
            # Создаем пустую базу данных, если её нет
            try:
                import sqlite3
                conn = sqlite3.connect(DB_FILE)
                conn.close()
                logger.info(f"Created new database at {DB_FILE}")
            except Exception as e:
                logger.error(f"Failed to create database at {DB_FILE}: {str(e)}", exc_info=True)
                abort(500, "Не удалось создать файл базы данных")
            
            # Проверяем, что файл создан
            if not os.path.exists(DB_FILE):
                logger.error(f"Database file was not created at {DB_FILE}")
                abort(500, "Файл базы данных не был создан")
        
        # Генерируем имя файла с датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"mafia_fantasy_backup_{timestamp}.db"
        
        logger.info(f"Sending database file for download: {DB_FILE}")
        
        # Отправляем файл
        return send_file(
            DB_FILE,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/x-sqlite3',
            conditional=True
        )
        
    except Exception as e:
        logger.error(f"Error downloading database: {str(e)}", exc_info=True)
        abort(500, f"Ошибка при загрузке базы данных: {str(e)}")

@backup_bp.route('/backup/list', methods=['GET'])
def list_backups():
    """Получить список доступных резервных копий"""
    try:
        logger.info("Listing available backups")
        
        # Создаем директорию, если она не существует
        os.makedirs(BACKUP_DIR, exist_ok=True)
        logger.debug(f"Backup directory: {BACKUP_DIR}")
        
        # Получаем список файлов в директории
        files = []
        try:
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith('.zip'):
                    file_path = os.path.join(BACKUP_DIR, filename)
                    if os.path.isfile(file_path):
                        try:
                            file_stat = os.stat(file_path)
                            files.append({
                                'name': filename,
                                'size': file_stat.st_size,
                                'created_at': file_stat.st_mtime,
                                'formatted_size': _format_file_size(file_stat.st_size),
                                'formatted_date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'download_url': f'/admin/backup/download/{filename}'
                            })
                        except Exception as e:
                            logger.error(f"Error getting file info for {file_path}: {str(e)}", exc_info=True)
                            continue
        except Exception as e:
            logger.error(f"Error reading backup directory: {str(e)}", exc_info=True)
            raise Exception("Ошибка при чтении директории с резервными копиями")
        
        # Сортируем по дате создания (новые сверху)
        files.sort(key=lambda x: x['created_at'], reverse=True)
        logger.info(f"Found {len(files)} backup files")
        
        return jsonify({
            'success': True,
            'backups': files,
            'total_backups': len(files),
            'total_size': sum(f['size'] for f in files),
            'formatted_total_size': _format_file_size(sum(f['size'] for f in files)) if files else '0 B'
        })
        
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Не удалось получить список резервных копий: {str(e)}"
        }), 500

def _format_file_size(size_bytes):
    """Форматирует размер файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_backup_list():
    """Получить список резервных копий (для обратной совместимости)"""
    try:
        # Используем существующий маршрут для получения списка бэкапов
        response = list_backups()
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                # Преобразуем формат ответа в старый формат
                return [{
                    'filename': b['name'],
                    'size': b['size'],
                    'created': b['created_at'],
                    'formatted_size': b.get('formatted_size', _format_file_size(b['size']))
                } for b in data.get('backups', [])]
        return []
    except Exception as e:
        logger.error(f"Error in get_backup_list: {str(e)}", exc_info=True)
        return []
