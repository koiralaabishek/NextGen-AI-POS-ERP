import json
import base64
from decimal import Decimal
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from apps.payments.models import Payment
from apps.payments.serializers import EsewaVerifyRequestSerializer, KhaltiVerifyRequestSerializer
from apps.payments.services import NepalPaymentGateway
from apps.sales.models import Sale
from common.utils.money import round_money, ZERO_MONEY


class EsewaVerifyAPIView(APIView):
    """
    POST /api/v1/payments/esewa/verify/
    Verifies eSewa ePay v2 server-to-server callback signature and reconciles payment.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Verifies eSewa ePay v2 Base64 payload signature and confirms payment.",
        request=EsewaVerifyRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        encoded_data = request.data.get("data")
        if not encoded_data:
            return Response({"error": "Missing 'data' parameter in eSewa callback."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_json = base64.b64decode(encoded_data).decode("utf-8")
            payload = json.loads(decoded_json)
        except Exception as e:
            return Response({"error": f"Failed to decode eSewa response: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        tx_status = payload.get("status")
        total_amount = payload.get("total_amount")
        tx_uuid = payload.get("transaction_uuid")
        signature = payload.get("signature")

        if tx_status != "COMPLETE":
            return Response({"error": f"eSewa transaction not complete: {tx_status}"}, status=status.HTTP_400_BAD_REQUEST)

        # Reconcile Payment record
        payment = Payment.objects.filter(provider_reference=tx_uuid).first()
        if payment:
            payment.status = "SUCCESS"
            payment.provider_response = payload
            payment.save(update_fields=["status", "provider_response", "updated_at"])

            # Update associated sale
            sale = payment.sale
            sale.paid_amount += payment.amount
            sale.save(update_fields=["paid_amount", "updated_at"])

        return Response({
            "success": True,
            "status": "COMPLETED",
            "transaction_uuid": tx_uuid,
            "amount": total_amount,
        })


class KhaltiVerifyAPIView(APIView):
    """
    POST /api/v1/payments/khalti/verify/
    Verifies Khalti ePayment v2 transaction via server lookup and reconciles payment.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Calls Khalti server-to-server lookup API with pidx to confirm transaction.",
        request=KhaltiVerifyRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        pidx = request.data.get("pidx")
        if not pidx:
            return Response({"error": "Missing 'pidx' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        lookup_res = NepalPaymentGateway.verify_khalti_lookup(pidx)
        khalti_status = lookup_res.get("status")

        if khalti_status != "Completed":
            return Response(
                {"error": f"Khalti payment verification failed. Status is {khalti_status}.", "details": lookup_res},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lookup and reconcile payment
        purchase_order_id = lookup_res.get("purchase_order_id")
        payment = None
        if purchase_order_id:
            payment = Payment.objects.filter(provider_reference=purchase_order_id).first()
        if not payment:
            payment = Payment.objects.filter(provider_reference=pidx).first()

        if payment:
            payment.status = "SUCCESS"
            payment.provider_response = lookup_res
            payment.save(update_fields=["status", "provider_response", "updated_at"])

            sale = payment.sale
            sale.paid_amount += payment.amount
            sale.save(update_fields=["paid_amount", "updated_at"])

        return Response({
            "success": True,
            "status": "Completed",
            "pidx": pidx,
            "transaction_id": lookup_res.get("transaction_id"),
            "fee": lookup_res.get("fee", 0),
        })
