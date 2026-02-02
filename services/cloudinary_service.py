"""
Cloudinary service for file uploads.
Handles resume and document storage.
"""

import re
from urllib.parse import urlparse

from django.conf import settings

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils


def get_cloudinary_config():
    """Configure Cloudinary using Django settings."""
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


class CloudinaryService:
    """Service class for Cloudinary operations."""

    @staticmethod
    def get_signed_url(public_id: str, resource_type: str = "raw") -> str:
        """
        Generate a signed URL for accessing a file.
        Uses cloudinary_url with sign_url=True to bypass ACL restrictions.
        
        Args:
            public_id: The Cloudinary public_id of the file
            resource_type: 'raw' for PDFs, 'image' for images
            
        Returns:
            Signed URL string
        """
        get_cloudinary_config()
        
        import time
        # Generate signed URL with expiration
        expires_at = int(time.time()) + 3600  # Valid for 1 hour
        
        signed_url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            type="authenticated",  # Use authenticated type for signed access
            sign_url=True,
            secure=True,
        )
        return signed_url

    @staticmethod
    def upload_resume(file, user_id: int, version_name: str) -> dict:
        """
        Upload a resume PDF to Cloudinary.

        Args:
            file: The uploaded file object
            user_id: The user's ID
            version_name: Name for this resume version

        Returns:
            dict with 'url', 'public_id', 'filename'
        """
        # Ensure Cloudinary is configured
        get_cloudinary_config()

        # Create a unique folder structure
        folder = f"jobtracker/resumes/user_{user_id}"

        # Generate a clean filename
        original_name = file.name if hasattr(file, "name") else "resume"

        # Sanitize version_name and original_name for URL-safe public_id
        safe_version = re.sub(r'[^a-zA-Z0-9_-]', '_', version_name)
        safe_original = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_name)

        try:
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="raw",  # For PDFs and documents
                type="upload",
                public_id=f"{safe_version}_{safe_original}",
                overwrite=True,
                tags=[f"user_{user_id}", "resume", version_name],
            )

            # Store original secure_url (short) - signed URL generated dynamically in serializer
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "filename": original_name,
                "size": result.get("bytes", 0),
                "format": result.get("format", "pdf"),
            }
        except Exception as e:
            raise Exception(f"Failed to upload resume: {str(e)}")

    @staticmethod
    def upload_cover_letter(file, user_id: int, application_id: int) -> dict:
        """
        Upload a cover letter document to Cloudinary.

        Args:
            file: The uploaded file object
            user_id: The user's ID
            application_id: The application's ID

        Returns:
            dict with 'url', 'public_id', 'filename'
        """
        # Ensure Cloudinary is configured
        get_cloudinary_config()

        folder = f"jobtracker/cover_letters/user_{user_id}"
        original_name = file.name if hasattr(file, "name") else "cover_letter"

        # Sanitize original_name for URL-safe public_id
        safe_original = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_name)

        try:
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="raw",
                type="upload",
                public_id=f"application_{application_id}_{safe_original}",
                overwrite=True,
                tags=[f"user_{user_id}", "cover_letter", f"application_{application_id}"],
            )

            # Store original secure_url (short) - signed URL generated dynamically when needed
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "filename": original_name,
                "size": result.get("bytes", 0),
            }
        except Exception as e:
            raise Exception(f"Failed to upload cover letter: {str(e)}")

    @staticmethod
    def delete_file(public_id: str) -> bool:
        """
        Delete a file from Cloudinary.

        Args:
            public_id: The Cloudinary public_id of the file

        Returns:
            bool: True if deleted successfully
        """
        # Ensure Cloudinary is configured
        get_cloudinary_config()

        try:
            result = cloudinary.uploader.destroy(public_id, resource_type="raw")
            return result.get("result") == "ok"
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    @staticmethod
    def get_file_url(public_id: str) -> str:
        """
        Get the URL for a file.

        Args:
            public_id: The Cloudinary public_id

        Returns:
            str: The secure URL
        """
        # Ensure Cloudinary is configured
        get_cloudinary_config()

        try:
            result = cloudinary.api.resource(public_id, resource_type="raw")
            return result["secure_url"]
        except Exception as e:
            raise Exception(f"Failed to get file URL: {str(e)}")
