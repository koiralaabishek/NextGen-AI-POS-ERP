from django.db import models
from django.conf import settings
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class AIConversation(TenantScopedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    title = models.CharField(max_length=255, default="New Conversation")

    class Meta:
        db_table = "ai_conversations"
        ordering = ["-updated_at"]


class AIMessage(UUIDBaseModel, TimestampedModel):
    SENDER_CHOICES = [
        ("USER", "User"),
        ("ASSISTANT", "AI Assistant"),
        ("TOOL", "System Tool Result"),
    ]
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_messages"
        ordering = ["created_at"]


class AIToolCall(UUIDBaseModel, TimestampedModel):
    message = models.ForeignKey(AIMessage, on_delete=models.CASCADE, related_name="tool_calls")
    tool_name = models.CharField(max_length=100)
    arguments_json = models.JSONField(default=dict)
    result_json = models.JSONField(default=dict)
    execution_time_ms = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_tool_calls"


class ForecastRun(TenantScopedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100, default="xgboost_demand_forecaster")
    target_metric = models.CharField(max_length=50, default="daily_sales_quantity")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "forecast_runs"


class ForecastResult(UUIDBaseModel):
    forecast_run = models.ForeignKey(ForecastRun, on_delete=models.CASCADE, related_name="results")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE)
    target_date = models.DateField()
    predicted_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    confidence_lower = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    confidence_upper = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "forecast_results"
        unique_together = ("forecast_run", "variant", "target_date")
