from datetime import datetime
from database import db

class Photo(db.Model):
    """Photo model for storing photo data and metadata"""
    
    __tablename__ = 'photos'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Photo data as base64 encoded string
    data = db.Column(db.Text, nullable=False)
    
    # File type (e.g., 'png', 'jpg', 'jpeg')
    file_type = db.Column(db.String(10), nullable=False)
    
    # Original file path
    path = db.Column(db.String(1000), nullable=False)
    
    # Location as string
    location = db.Column(db.String(500), nullable=True)
    
    # Timestamps for tracking
    timestamp = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Photo {self.id}: {self.file_type} at {self.location or "unknown location"}>'
    
    def to_dict(self):
        """Convert Photo object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'data': self.data,
            'file_type': self.file_type,
            'path': self.path,
            'location': self.location,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def create_photo(cls, data, file_type, path=None, location=None, timestamp=None):
        """Create a new photo record"""
        photo = cls(
            data=data,
            file_type=file_type,
            path=path,
            location=location,
            timestamp=timestamp
        )
        db.session.add(photo)
        db.session.commit()
        return photo
    
    def update_location(self, location):
        """Update the location of the photo"""
        self.location = location
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the photo record"""
        db.session.delete(self)
        db.session.commit() 