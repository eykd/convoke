"""Flexible application configuration"""
from contextvars import ContextVar

current_hq = ContextVar("current_hq")
