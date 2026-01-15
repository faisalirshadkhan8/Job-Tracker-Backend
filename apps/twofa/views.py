"""
Two-Factor Authentication Views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .serializers import (
    TwoFactorSetupSerializer,
    TwoFactorConfirmSerializer,
    TwoFactorVerifySerializer,
    TwoFactorDisableSerializer,
    TwoFactorStatusSerializer,
    BackupCodesRegenerateSerializer,
    BackupCodesResponseSerializer,
)
from .services import TwoFactorService


class TwoFactorStatusView(APIView):
    """Get 2FA status for current user."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get 2FA Status",
        description="Get the current 2FA status for your account.",
        responses={200: TwoFactorStatusSerializer},
        tags=["Two-Factor Authentication"]
    )
    def get(self, request):
        status_data = TwoFactorService.get_status(request.user)
        return Response(status_data)


class TwoFactorSetupView(APIView):
    """Set up 2FA for current user."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Setup 2FA",
        description="""
        Initialize 2FA setup for your account.
        
        Returns a QR code to scan with an authenticator app and backup codes.
        You must call the confirm endpoint with a valid code to complete setup.
        
        **Important:** Save the backup codes securely - they can be used for recovery.
        """,
        responses={200: TwoFactorSetupSerializer},
        tags=["Two-Factor Authentication"]
    )
    def post(self, request):
        try:
            secret, qr_code, backup_codes = TwoFactorService.setup_2fa(request.user)
            
            import pyotp
            totp = pyotp.TOTP(secret)
            otpauth_url = totp.provisioning_uri(
                name=request.user.email,
                issuer_name='Job Application Tracker'
            )
            
            return Response({
                'secret': secret,
                'qr_code': qr_code,
                'backup_codes': backup_codes,
                'otpauth_url': otpauth_url,
                'message': 'Scan the QR code with your authenticator app, then confirm with a code.'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorConfirmView(APIView):
    """Confirm 2FA setup with initial code."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Confirm 2FA Setup",
        description="Confirm 2FA setup by providing a valid code from your authenticator app.",
        request=TwoFactorConfirmSerializer,
        tags=["Two-Factor Authentication"]
    )
    def post(self, request):
        serializer = TwoFactorConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        if TwoFactorService.confirm_setup(request.user, code):
            return Response({
                'message': '2FA has been enabled for your account.',
                'enabled': True
            })
        else:
            return Response(
                {'error': 'Invalid code. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorVerifyView(APIView):
    """Verify 2FA code (for login)."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Verify 2FA Code",
        description="Verify a 2FA code. Use either a TOTP code or a backup code.",
        request=TwoFactorVerifySerializer,
        tags=["Two-Factor Authentication"]
    )
    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        # Try TOTP first, then backup code
        if TwoFactorService.verify_totp(request.user, code):
            return Response({
                'verified': True,
                'method': 'totp'
            })
        elif TwoFactorService.verify_backup_code(request.user, code):
            return Response({
                'verified': True,
                'method': 'backup_code',
                'warning': 'Backup code used. Consider regenerating your backup codes.'
            })
        else:
            return Response(
                {'error': 'Invalid code.', 'verified': False},
                status=status.HTTP_401_UNAUTHORIZED
            )


class TwoFactorDisableView(APIView):
    """Disable 2FA for current user."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Disable 2FA",
        description="Disable 2FA for your account. Requires password and 2FA code confirmation.",
        request=TwoFactorDisableSerializer,
        tags=["Two-Factor Authentication"]
    )
    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify password
        if not request.user.check_password(serializer.validated_data['password']):
            return Response(
                {'error': 'Invalid password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        
        if TwoFactorService.disable_2fa(request.user, code):
            return Response({
                'message': '2FA has been disabled for your account.',
                'enabled': False
            })
        else:
            return Response(
                {'error': 'Invalid code or 2FA not enabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class BackupCodesRegenerateView(APIView):
    """Regenerate backup codes."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Regenerate Backup Codes",
        description="""
        Generate new backup codes. This invalidates all existing unused backup codes.
        
        Requires a valid TOTP code for verification.
        """,
        request=BackupCodesRegenerateSerializer,
        responses={200: BackupCodesResponseSerializer},
        tags=["Two-Factor Authentication"]
    )
    def post(self, request):
        serializer = BackupCodesRegenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        new_codes = TwoFactorService.regenerate_backup_codes(request.user, code)
        
        if new_codes:
            return Response({
                'backup_codes': new_codes,
                'message': 'Backup codes regenerated. Save these securely.'
            })
        else:
            return Response(
                {'error': 'Invalid code or 2FA not enabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
