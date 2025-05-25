"""
Email data models and storage for MCP email inbox simulation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    FORWARDED = "forwarded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EmailAttachment(BaseModel):
    filename: str
    size: int  # in bytes
    content_type: str
    attachment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class Email(BaseModel):
    email_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    sender: str
    recipients: List[str]
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    body: str
    html_body: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    status: EmailStatus = EmailStatus.UNREAD
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: List[EmailAttachment] = Field(default_factory=list)
    folder: str = "inbox"
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class EmailFolder(BaseModel):
    name: str
    email_count: int = 0
    unread_count: int = 0


class EmailInbox(BaseModel):
    """In-memory email storage and management."""
    emails: Dict[str, Email] = Field(default_factory=dict)
    folders: Dict[str, EmailFolder] = Field(default_factory=lambda: {
        "inbox": EmailFolder(name="inbox"),
        "sent": EmailFolder(name="sent"),
        "drafts": EmailFolder(name="drafts"),
        "trash": EmailFolder(name="trash"),
        "spam": EmailFolder(name="spam"),
        "archive": EmailFolder(name="archive")
    })
    
    def add_email(self, email: Email) -> str:
        """Add an email to the inbox."""
        self.emails[email.email_id] = email
        self._update_folder_counts(email.folder)
        return email.email_id
    
    def get_email(self, email_id: str) -> Optional[Email]:
        """Get an email by ID."""
        return self.emails.get(email_id)
    
    def list_emails(self, folder: str = "inbox", limit: int = 50, offset: int = 0) -> List[Email]:
        """List emails in a folder."""
        folder_emails = [
            email for email in self.emails.values() 
            if email.folder == folder and email.status != EmailStatus.DELETED
        ]
        # Sort by timestamp, newest first
        folder_emails.sort(key=lambda x: x.timestamp, reverse=True)
        return folder_emails[offset:offset + limit]
    
    def search_emails(self, query: str, folder: Optional[str] = None) -> List[Email]:
        """Search emails by subject, sender, or body content."""
        query_lower = query.lower()
        results = []
        
        for email in self.emails.values():
            if email.status == EmailStatus.DELETED:
                continue
            if folder and email.folder != folder:
                continue
                
            # Search in subject, sender, body
            if (query_lower in email.subject.lower() or 
                query_lower in email.sender.lower() or 
                query_lower in email.body.lower()):
                results.append(email)
        
        # Sort by timestamp, newest first
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        email = self.emails.get(email_id)
        if email and email.status == EmailStatus.UNREAD:
            email.status = EmailStatus.READ
            self._update_folder_counts(email.folder)
            return True
        return False
    
    def move_email(self, email_id: str, target_folder: str) -> bool:
        """Move an email to a different folder."""
        email = self.emails.get(email_id)
        if email and target_folder in self.folders:
            old_folder = email.folder
            email.folder = target_folder
            self._update_folder_counts(old_folder)
            self._update_folder_counts(target_folder)
            return True
        return False
    
    def delete_email(self, email_id: str) -> bool:
        """Delete an email (move to trash or permanent delete)."""
        email = self.emails.get(email_id)
        if email:
            if email.folder == "trash":
                # Permanent delete
                del self.emails[email_id]
            else:
                # Move to trash
                old_folder = email.folder
                email.folder = "trash"
                email.status = EmailStatus.DELETED
                self._update_folder_counts(old_folder)
                self._update_folder_counts("trash")
            return True
        return False
    
    def _update_folder_counts(self, folder_name: str):
        """Update email and unread counts for a folder."""
        if folder_name not in self.folders:
            return
            
        folder_emails = [
            email for email in self.emails.values() 
            if email.folder == folder_name and email.status != EmailStatus.DELETED
        ]
        
        self.folders[folder_name].email_count = len(folder_emails)
        self.folders[folder_name].unread_count = len([
            email for email in folder_emails 
            if email.status == EmailStatus.UNREAD
        ])


# Global inbox instance
email_inbox = EmailInbox() 